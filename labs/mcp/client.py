"""Unified MCP client for schema retrieval and validation."""

from __future__ import annotations

import copy
import logging
import os
import threading
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

from labs.logging import log_jsonl
from labs.mcp.exceptions import MCPUnavailableError
from labs.mcp.tcp_client import TcpMCPValidator, get_schema_from_mcp

JsonDict = Dict[str, Any]

_LOGGER = logging.getLogger("labs.mcp.client")
_DEFAULT_SCHEMA_NAME = "synesthetic-asset"
_VALID_RESOLUTIONS = {"inline"}


class MCPClientError(RuntimeError):
    """Base error raised by the MCP client."""


class MCPValidationError(MCPClientError):
    """Raised when MCP validation returns a non-OK payload."""

    def __init__(self, result: Mapping[str, Any]) -> None:
        message = result.get("reason") if isinstance(result, Mapping) else "validation_failed"
        super().__init__(f"MCP validation failed: {message}")
        self.result = result


class MCPClient:
    """Encapsulate schema retrieval, resolution, and validation handshakes."""

    DEFAULT_BATCH_LIMIT = 50

    def __init__(
        self,
        *,
        schema_name: str = _DEFAULT_SCHEMA_NAME,
        schema_version: Optional[str] = None,
        resolution: Optional[str] = None,
        batch_limit: Optional[int] = None,
        telemetry_path: Optional[str] = None,
        event_hook: Optional[Callable[[JsonDict], None]] = None,
        tcp_validator: Optional[TcpMCPValidator] = None,
    ) -> None:
        self.schema_name = schema_name or _DEFAULT_SCHEMA_NAME
        self._requested_version = schema_version or os.getenv(
            "LABS_SCHEMA_VERSION", "0.7.4"
        )
        env_resolution = os.getenv("LABS_SCHEMA_RESOLUTION")
        self.resolution = self._normalise_resolution(resolution or env_resolution)
        self.batch_limit = self._resolve_batch_limit(batch_limit)
        self.telemetry_path = telemetry_path or os.getenv("LABS_MCP_LOG_PATH")
        self._event_hook = event_hook
        self._descriptor_cache: Dict[Tuple[str, str, str], JsonDict] = {}
        self._descriptor: Optional[JsonDict] = None
        self._tcp_validator = tcp_validator
        self._lock = threading.RLock()

    @staticmethod
    def _normalise_resolution(resolution: Optional[str]) -> str:
        base = resolution.strip().lower() if isinstance(resolution, str) else None
        value = base or 'inline'
        if value not in _VALID_RESOLUTIONS:
            _LOGGER.warning("Unsupported schema resolution '%s'; forcing inline", resolution)
        elif value != 'inline':
            _LOGGER.info("Forcing inline schema resolution (requested '%s')", resolution)
        return 'inline'

    @staticmethod
    def _resolve_batch_limit(candidate: Optional[int]) -> int:
        if candidate is not None and candidate > 0:
            return candidate
        env_value = os.getenv("MCP_MAX_BATCH")
        if env_value:
            try:
                parsed = int(env_value)
            except ValueError:
                _LOGGER.warning("Invalid MCP_MAX_BATCH value '%s'; using default", env_value)
            else:
                if parsed > 0:
                    return parsed
        return MCPClient.DEFAULT_BATCH_LIMIT

    @property
    def descriptor(self) -> Optional[JsonDict]:
        with self._lock:
            if self._descriptor is None:
                return None
            return copy.deepcopy(self._descriptor)

    @property
    def schema_version(self) -> str:
        with self._lock:
            if self._descriptor and isinstance(self._descriptor.get("version"), str):
                return self._descriptor["version"]
        return self._requested_version

    @property
    def schema_id(self) -> Optional[str]:
        descriptor = self.descriptor
        if descriptor:
            schema = descriptor.get("schema")
            if isinstance(schema, Mapping):
                schema_id = schema.get("$id")
                if isinstance(schema_id, str) and schema_id.strip():
                    return schema_id
            schema_id = descriptor.get("schema_id")
            if isinstance(schema_id, str):
                return schema_id
        return None

    def fetch_schema(
        self,
        name: Optional[str] = None,
        *,
        version: Optional[str] = None,
        resolution: Optional[str] = None,
        force: bool = False,
    ) -> JsonDict:
        """Retrieve and cache the descriptor for *name*."""

        target_name = name or self.schema_name
        target_version = version or self._requested_version
        target_resolution = self._normalise_resolution(resolution or self.resolution)

        cache_key = (target_name, target_version, target_resolution)
        with self._lock:
            if not force and cache_key in self._descriptor_cache:
                self._descriptor = self._descriptor_cache[cache_key]
                return copy.deepcopy(self._descriptor)

        descriptor = self._resolve_schema_descriptor(
            target_name, target_version, target_resolution
        )

        with self._lock:
            self._descriptor_cache[cache_key] = descriptor
            self._descriptor = descriptor

        self._emit_event(
            {
                "event": "schema_fetched",
                "schema_name": descriptor.get("name"),
                "schema_version": descriptor.get("version"),
                "schema_resolution": descriptor.get("resolution"),
                "schema_id": descriptor.get("schema_id"),
            }
        )
        return copy.deepcopy(descriptor)

    def validate(
        self,
        assets: Sequence[MutableMapping[str, Any]] | Iterable[MutableMapping[str, Any]],
        *,
        strict: bool = True,
    ) -> List[JsonDict]:
        """Validate *assets* via MCP batch validation."""

        batch = list(assets)
        if not batch:
            return []
        if len(batch) > self.batch_limit:
            raise MCPClientError(f"validation batch exceeds limit {self.batch_limit}")

        prepared_batch = [self._prepare_asset_for_validation(item) for item in batch]

        validator = self._require_tcp_validator()
        results: List[JsonDict] = []

        for asset in prepared_batch:
            try:
                response = validator.validate(asset)
            except MCPUnavailableError:
                raise
            except Exception as exc:  # pragma: no cover - defensive guard
                raise MCPUnavailableError(f"MCP validation failed: {exc}") from exc
            if not isinstance(response, Mapping):
                raise MCPUnavailableError("Invalid MCP response payload")
            results.append(dict(response))
        self._emit_event(
            {
                "event": "schema_validated",
                "count": len(results),
                "strict": strict,
                "ok": all(entry.get("ok") for entry in results),
            }
        )
        return results

    def confirm(self, asset: MutableMapping[str, Any], *, strict: bool = True) -> JsonDict:
        """Validate a single *asset* and raise on failure when strict."""

        results = self.validate([asset], strict=strict)
        if not results:
            raise MCPValidationError({"ok": False, "reason": "empty_result"})
        result = results[0]
        if strict and not result.get("ok"):
            raise MCPValidationError(result)
        return result

    def _resolve_schema_descriptor(
        self,
        name: str,
        version: str,
        resolution: str,
    ) -> JsonDict:
        response: Optional[JsonDict] = None
        try:
            response = get_schema_from_mcp(
                name,
                version=version,
                resolution=resolution,
            )
        except MCPUnavailableError:
            raise
        except Exception as exc:  # pragma: no cover - unexpected transport failure
            raise MCPUnavailableError(f"MCP schema fetch failed: {exc}") from exc

        if not isinstance(response, Mapping):
            raise MCPUnavailableError("MCP schema response must be a mapping")
        if response.get("ok") is not True:
            reason = response.get("reason", "schema_unavailable")
            raise MCPUnavailableError(f"MCP schema unavailable: {reason}")

        schema = response.get("schema")
        if not isinstance(schema, Mapping):
            raise MCPUnavailableError("MCP schema payload missing 'schema'")

        resolved_version = response.get("version") or version or self._requested_version

        descriptor: JsonDict = {
            "ok": True,
            "name": response.get("name", name),
            "version": resolved_version,
            "path": response.get("path"),
            "schema": copy.deepcopy(schema),
            "resolution": resolution,
            "fetched_at": datetime.now(tz=timezone.utc).isoformat(),
        }
        schema_id = schema.get("$id")
        if isinstance(schema_id, str) and schema_id.strip():
            descriptor["schema_id"] = schema_id
        return descriptor

    def _emit_event(self, record: JsonDict) -> None:
        if not record:
            return
        enriched = dict(record)
        enriched.setdefault("ts", datetime.now(tz=timezone.utc).isoformat())
        if self.telemetry_path:
            try:
                log_jsonl(self.telemetry_path, enriched)
            except Exception as exc:  # pragma: no cover - logging failures shouldn't break flow
                _LOGGER.debug("Failed to write MCP telemetry: %s", exc)
        if self._event_hook:
            try:
                self._event_hook(enriched)
            except Exception as exc:  # pragma: no cover - user hook failure should not propagate
                _LOGGER.debug("MCPClient event hook failed: %s", exc)

    def record_event(self, event: str, **fields: Any) -> None:
        """Emit a lifecycle telemetry record with arbitrary metadata."""

        if not isinstance(event, str) or not event:
            raise ValueError("event must be a non-empty string")
        payload: JsonDict = {"event": event}
        payload.update(fields)
        self._emit_event(payload)

    def _require_tcp_validator(self) -> TcpMCPValidator:
        with self._lock:
            if self._tcp_validator is None:
                host = os.getenv("MCP_HOST", "127.0.0.1").strip()
                port_raw = os.getenv("MCP_PORT", "8765").strip()
                timeout_raw = os.getenv("MCP_TIMEOUT", "10.0").strip()
                if not host:
                    raise MCPUnavailableError("MCP_HOST is required for TCP transport")
                try:
                    port = int(port_raw)
                except ValueError as exc:  # pragma: no cover - defensive
                    raise MCPUnavailableError("MCP_PORT must be an integer") from exc
                try:
                    timeout = float(timeout_raw)
                except ValueError as exc:  # pragma: no cover - defensive
                    raise MCPUnavailableError("MCP_TIMEOUT must be numeric") from exc
                self._tcp_validator = TcpMCPValidator(host, port, timeout=timeout)
            return self._tcp_validator

    def _prepare_asset_for_validation(self, asset: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
        payload = copy.deepcopy(asset)
        version = self._extract_schema_version(payload)
        if version and self._is_legacy_version(version):
            self._strip_legacy_metadata(payload)
        return payload

    def _extract_schema_version(self, asset: Mapping[str, Any]) -> Optional[str]:
        schema_field = asset.get("$schema")
        if isinstance(schema_field, str) and schema_field.strip():
            tokens = schema_field.rstrip("/").split("/")
            if tokens:
                candidate = tokens[-2] if len(tokens) >= 2 else tokens[-1]
                if candidate and all(ch.isdigit() or ch == "." for ch in candidate):
                    return candidate
        return self.schema_version

    @staticmethod
    def _parse_version(value: Optional[str]) -> Optional[Tuple[int, int, int]]:
        if not value:
            return None
        try:
            parts = tuple(int(part) for part in str(value).split("."))
        except ValueError:
            return None
        if len(parts) != 3:
            return None
        return parts  # type: ignore[return-value]

    def _is_legacy_version(self, version: str) -> bool:
        parsed = self._parse_version(version)
        if parsed is None:
            return str(version) < "0.7.4"
        return parsed < (0, 7, 4)

    @staticmethod
    def _strip_legacy_metadata(payload: MutableMapping[str, Any]) -> None:
        for key in ("asset_id", "prompt", "timestamp", "seed", "parameter_index", "provenance"):
            payload.pop(key, None)
        meta_info = payload.get("meta_info")
        if isinstance(meta_info, MutableMapping):
            meta_info.pop("provenance", None)
        # Legacy schema disallows embedded telemetry fields under rule_bundle meta.
        rule_bundle = payload.get("rule_bundle")
        if isinstance(rule_bundle, MutableMapping):
            bundle_meta = rule_bundle.get("meta_info")
            if isinstance(bundle_meta, MutableMapping):
                bundle_meta.pop("provenance", None)


def load_schema_bundle(
    *,
    schema_name: str = _DEFAULT_SCHEMA_NAME,
    version: Optional[str] = None,
    client: Optional["MCPClient"] = None,
) -> Dict[str, Any]:
    """Fetch and return the authoritative inline schema bundle without disk IO."""

    active_client = client or MCPClient(schema_name=schema_name, schema_version=version, resolution='inline')
    descriptor = active_client.fetch_schema(
        schema_name,
        version=version,
        resolution='inline',
        force=client is None,
    )
    schema = descriptor.get("schema")
    if not isinstance(schema, Mapping):
        raise MCPClientError("MCP schema response missing inline bundle")
    return copy.deepcopy(schema)


__all__ = ["MCPClient", "MCPClientError", "MCPValidationError", "load_schema_bundle"]
