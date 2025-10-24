"""Unified MCP client for schema retrieval and validation."""

from __future__ import annotations

import copy
import logging
import os
import threading
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple, Union

from mcp import core as mcp_core

from labs.generator.assembler import AssetAssembler
from labs.logging import log_jsonl
from labs.mcp.exceptions import MCPUnavailableError
from labs.mcp.tcp_client import get_schema_from_mcp

JsonDict = Dict[str, Any]

_LOGGER = logging.getLogger("labs.mcp.client")
_DEFAULT_SCHEMA_NAME = "synesthetic-asset"
_VALID_RESOLUTIONS = {"preserve", "inline", "bundled"}


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
    ) -> None:
        self.schema_name = schema_name or _DEFAULT_SCHEMA_NAME
        self._requested_version = schema_version or os.getenv(
            "LABS_SCHEMA_VERSION", AssetAssembler.DEFAULT_SCHEMA_VERSION
        )
        env_resolution = os.getenv("LABS_SCHEMA_RESOLUTION")
        self.resolution = self._normalise_resolution(resolution or env_resolution)
        self.batch_limit = self._resolve_batch_limit(batch_limit)
        self.telemetry_path = telemetry_path or os.getenv("LABS_MCP_LOG_PATH")
        self._event_hook = event_hook
        self._descriptor_cache: Dict[Tuple[str, str, str], JsonDict] = {}
        self._descriptor: Optional[JsonDict] = None
        self._transport_validator: Union[Callable[[MutableMapping[str, Any]], Dict[str, Any]], bool, None] = None
        self._lock = threading.RLock()

    @staticmethod
    def _normalise_resolution(resolution: Optional[str]) -> str:
        base = resolution.strip().lower() if isinstance(resolution, str) else None
        value = base or "inline"
        if value not in _VALID_RESOLUTIONS:
            _LOGGER.warning("Unsupported schema resolution '%s'; falling back to inline", resolution)
            return "inline"
        return value

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

        transport_validator = self._resolve_transport_validator()
        results: Optional[List[JsonDict]] = None

        if callable(transport_validator):
            responses: List[JsonDict] = []
            for asset in prepared_batch:
                try:
                    response = transport_validator(asset)
                except MCPUnavailableError as exc:
                    _LOGGER.debug("Transport validator unavailable during batch validation: %s", exc)
                    self._transport_validator = False
                    responses = []
                    break
                except Exception as exc:  # pragma: no cover - defensive fallback
                    _LOGGER.warning("Unexpected MCP transport validation error: %s", exc)
                    self._transport_validator = False
                    responses = []
                    break
                if isinstance(response, Mapping):
                    responses.append(dict(response))
                else:
                    responses.append({"ok": False, "reason": "invalid_mcp_response"})
            if responses:
                results = responses

        if results is None:
            payload = mcp_core.validate_many(prepared_batch, strict=strict)
            results = self._normalise_validation_payload(payload)
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
        except MCPUnavailableError as exc:
            _LOGGER.debug("TCP MCP unavailable for schema fetch (%s); falling back to local", exc)
        except Exception as exc:  # pragma: no cover - unexpected transport failure
            _LOGGER.warning("Unexpected MCP error during schema fetch: %s", exc)

        if not response:
            response = mcp_core.get_schema(name, version=version, resolution=resolution)

        if not isinstance(response, Mapping):
            raise MCPClientError("MCP schema response must be a mapping")
        if response.get("ok") is False:
            reason = response.get("reason", "schema_unavailable")
            if version and isinstance(reason, str) and "schema_not_found" in reason:
                fallback = mcp_core.get_schema(name, resolution=resolution)
                if not isinstance(fallback, Mapping) or not fallback.get("ok"):
                    raise MCPClientError(f"MCP schema unavailable: {reason}")
                _LOGGER.debug(
                    "Schema version %s unavailable; falling back to %s",
                    version,
                    fallback.get("version"),
                )
                response = fallback
            else:
                raise MCPClientError(f"MCP schema unavailable: {reason}")

        schema = response.get("schema")
        if not isinstance(schema, Mapping):
            raise MCPClientError("MCP schema payload missing 'schema'")

        source_version = response.get("version") or version
        requested_version = response.get("requested_version")
        resolved_version = requested_version or source_version or version

        schema_id = schema.get("$id")
        if requested_version and isinstance(requested_version, str) and requested_version.strip():
            schema_id = AssetAssembler.schema_url(requested_version)
        elif not isinstance(schema_id, str) or not schema_id.strip():
            schema_id = AssetAssembler.schema_url(resolved_version)

        descriptor: JsonDict = {
            "ok": True,
            "name": response.get("name", name),
            "version": resolved_version,
            "path": response.get("path"),
            "schema": copy.deepcopy(schema),
            "schema_id": schema_id,
            "resolution": resolution,
            "fetched_at": datetime.now(tz=timezone.utc).isoformat(),
        }
        if requested_version:
            descriptor["requested_version"] = requested_version
        if source_version and source_version != resolved_version:
            descriptor["source_version"] = source_version
        schema_copy = descriptor.get("schema")
        if requested_version and isinstance(schema_copy, MutableMapping):
            schema_copy["$id"] = schema_id
        return descriptor

    @staticmethod
    def _normalise_validation_payload(payload: Any) -> List[JsonDict]:
        if isinstance(payload, list):
            return [copy.deepcopy(entry) for entry in payload if isinstance(entry, Mapping)]
        if isinstance(payload, Mapping):
            items = payload.get("items")
            if isinstance(items, list):
                return [copy.deepcopy(entry) for entry in items if isinstance(entry, Mapping)]
            return [copy.deepcopy(payload)]
        raise MCPClientError("Unexpected MCP validation response payload")

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

    def _resolve_transport_validator(self) -> Optional[Callable[[MutableMapping[str, Any]], Dict[str, Any]]]:
        cached = self._transport_validator
        if cached is False:
            return None
        if callable(cached):
            return cached
        try:
            from labs.mcp_stdio import build_validator_from_env  # local import to avoid cycles
        except ImportError:
            self._transport_validator = False
            return None
        try:
            validator = build_validator_from_env()
        except MCPUnavailableError:
            self._transport_validator = False
            return None
        self._transport_validator = validator
        return validator

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


__all__ = ["MCPClient", "MCPClientError", "MCPValidationError"]
