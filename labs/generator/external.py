"""External generator integrations for Synesthetic Labs."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import logging
import os
import random
import socket
import time
import urllib.error
import urllib.request
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
import uuid
from copy import deepcopy
from functools import lru_cache
from numbers import Real
from typing import Any, Callable, Dict, List, Optional, Tuple

import requests

from mcp.core import get_schema
from labs.generator.assembler import AssetAssembler
from labs.logging import log_external_generation

JsonDict = Dict[str, Any]

MAX_REQUEST_BYTES = 256 * 1024
MAX_RESPONSE_BYTES = 1024 * 1024
_DEFAULT_BACKOFF_BASE_SECONDS = 0.2
_BACKOFF_FACTOR = 2.0
_BACKOFF_CAP_SECONDS = 5.0
_JITTER_FRACTION = 0.2

SENSITIVE_HEADERS = {"authorization", "x-goog-api-key"}

_DEFAULT_SECTIONS = {
    "shader": {"input_parameters": []},
    "tone": {"input_parameters": []},
    "haptic": {"input_parameters": []},
    "control": {"control_parameters": []},
    "meta_info": {},
    "rule_bundle": {"rules": [], "meta_info": {}},
}
_DEFAULT_MODULATIONS: List[Dict[str, Any]] = []
_DEFAULT_CONTROL_PARAMETERS: List[Dict[str, Any]] = [
    {
        "id": "mouse_x_shader_px",
        "parameter": "shader.u_px",
        "label": "mouse.x",
        "unit": "normalized",
        "sensitivity": 1.0,
        "combo": [
            {
                "device": "mouse",
                "control": "x",
            }
        ],
        "mode": "absolute",
        "curve": "linear",
        "range": {"minimum": -1.0, "maximum": 1.0},
    },
    {
        "id": "mouse_y_shader_py",
        "parameter": "shader.u_py",
        "label": "mouse.y",
        "unit": "normalized",
        "sensitivity": 1.0,
        "combo": [
            {
                "device": "mouse",
                "control": "y",
            }
        ],
        "mode": "absolute",
        "curve": "linear",
        "invert": True,
        "range": {"minimum": -1.0, "maximum": 1.0},
    },
]
_DEFAULT_PARAMETER_INDEX: List[str] = ["shader.u_px", "shader.u_py"]


def _normalize_schema_version(value: Optional[str]) -> str:
    if value is None:
        return AssetAssembler.DEFAULT_SCHEMA_VERSION
    normalized = str(value).strip()
    return normalized or AssetAssembler.DEFAULT_SCHEMA_VERSION


@lru_cache(maxsize=8)
def _cached_schema_descriptor(version: str) -> Tuple[str, str, Dict[str, Any]]:
    response = get_schema("synesthetic-asset", version=version)
    if not response.get("ok"):
        raise RuntimeError(f"Failed to load schema: {response}")

    schema = response.get("schema")
    if not isinstance(schema, dict):
        raise RuntimeError(f"Schema payload missing 'schema': {response}")

    schema_id = schema.get("$id") or AssetAssembler.schema_url(version)
    resolved_version = response.get("version") or version
    return schema_id, resolved_version, schema


def _schema_descriptor(version: Optional[str]) -> Tuple[str, str, Dict[str, Any]]:
    normalized = _normalize_schema_version(version)
    return _cached_schema_descriptor(normalized)


def _schema_default_for_property(spec: Any) -> Any:
    if isinstance(spec, dict):
        if "default" in spec:
            return deepcopy(spec["default"])
        if "$ref" in spec:
            return {}
        type_info = spec.get("type")
        if isinstance(type_info, list):
            if "object" in type_info:
                type_info = "object"
            elif "array" in type_info:
                type_info = "array"
            else:
                type_info = type_info[0]
        if type_info == "object":
            return {}
        if type_info == "array":
            return []
    return None


def _build_schema_skeleton(schema: Dict[str, Any]) -> JsonDict:
    skeleton: JsonDict = {}
    properties = schema.get("properties")
    if isinstance(properties, dict):
        for key, descriptor in properties.items():
            skeleton[key] = _schema_default_for_property(descriptor)

    skeleton.setdefault("shader", {})
    skeleton.setdefault("tone", {})
    skeleton.setdefault("haptic", {})
    skeleton.setdefault("control", {})
    skeleton.setdefault("meta_info", {})
    skeleton.setdefault("rule_bundle", {})
    skeleton.setdefault("modulations", [])
    skeleton.setdefault("meta", {})
    return skeleton


def _strict_mode_enabled() -> bool:
    raw = os.getenv("LABS_FAIL_FAST")
    if raw is None:
        return True
    lowered = raw.strip().lower()
    return lowered not in {"0", "false", "no", "off"}


class ExternalRequestError(RuntimeError):
    """Raised when an HTTP invocation fails with a classified taxonomy reason."""

    def __init__(
        self,
        reason: str,
        detail: str,
        *,
        status_code: Optional[int] = None,
        retryable: bool = True,
    ) -> None:
        super().__init__(detail)
        self.reason = reason
        self.detail = detail
        self.status_code = status_code
        self.retryable = retryable


class ExternalGenerationError(RuntimeError):
    """Raised when an external generator exhausts its retries."""

    def __init__(
        self,
        message: str,
        *,
        trace: JsonDict,
        reason: str,
        detail: str,
        cause: Optional[Exception] = None,
    ) -> None:
        super().__init__(message)
        self.trace = trace
        self.reason = reason
        self.detail = detail
        self.__cause__ = cause


class ExternalGenerator:
    """Base class for API-driven generators."""

    DEFAULT_LOG_PATH = "meta/output/labs/external.jsonl"
    DEFAULT_MAX_RETRIES = 3

    engine = "external"
    api_version = "unspecified"
    endpoint: Optional[str] = None

    api_key_env: Optional[str] = None
    endpoint_env: Optional[str] = None
    default_endpoint: Optional[str] = None

    def __init__(
        self,
        *,
        log_path: Optional[str] = None,
        transport: Optional[Callable[[JsonDict], JsonDict]] = None,
        mock_mode: Optional[bool] = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_seconds: float = _DEFAULT_BACKOFF_BASE_SECONDS,
        timeout_seconds: float = 35.0,
        sleeper: Callable[[float], None] = time.sleep,
        schema_version: Optional[str] = None,
    ) -> None:
        if max_retries < 1:
            raise ValueError("max_retries must be >= 1")
        if backoff_seconds <= 0:
            raise ValueError("backoff_seconds must be positive")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

        if mock_mode is None:
            mock_env = os.getenv("LABS_EXTERNAL_LIVE", "0").strip().lower()
            mock_mode = mock_env not in {"1", "true", "yes", "on"}

        self.log_path = log_path or self.DEFAULT_LOG_PATH
        self._transport = transport
        self.mock_mode = mock_mode
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.timeout_seconds = timeout_seconds
        self._sleep = sleeper
        self._logger = logging.getLogger(self.__class__.__name__)
        self.schema_version = schema_version or AssetAssembler.DEFAULT_SCHEMA_VERSION

    # Public API -----------------------------------------------------------------
    def generate(
        self,
        prompt: str,
        *,
        parameters: Optional[JsonDict] = None,
        seed: Optional[int] = None,
        timeout: Optional[float] = None,
        trace_id: Optional[str] = None,
        schema_version: Optional[str] = None,
    ) -> Tuple[JsonDict, JsonDict]:
        """Return an asset assembled from an external API response."""

        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")

        parameters = dict(parameters or {})
        defaults = self.default_parameters()
        for key, value in defaults.items():
            parameters.setdefault(key, value)
        if seed is not None:
            parameters.setdefault("seed", seed)

        resolved_schema_version = (
            schema_version
            or os.getenv("LABS_SCHEMA_VERSION", AssetAssembler.DEFAULT_SCHEMA_VERSION)
        )

        attempts: List[JsonDict] = []
        strict_mode = _strict_mode_enabled()
        run_trace_id = trace_id or str(uuid.uuid4())
        resolved_timeout = timeout or self.timeout_seconds

        final_error: Optional[ExternalRequestError] = None
        last_exception: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            request_envelope = self._request_envelope(prompt, parameters, run_trace_id)
            request_payload = self._build_request(request_envelope, prompt, parameters)
            request_bytes = self._encode_payload(request_payload)
            if len(request_bytes) > MAX_REQUEST_BYTES:
                final_error = ExternalRequestError(
                    "bad_response",
                    "request_body_exceeds_256KiB",
                    retryable=False,
                )
                break

            attempt_record: JsonDict = {
                "attempt": attempt,
                "request": request_payload,
            }

            if not self.mock_mode:
                try:
                    settings = self._resolve_live_settings()
                except ExternalRequestError as exc:
                    attempts.append(self._record_failure_attempt(attempt_record, exc.reason, exc.detail))
                    final_error = exc
                    last_exception = exc
                    break
                attempt_record["request_headers"] = settings["log_headers"]
                endpoint = settings["endpoint"]
            else:
                settings = {"endpoint": self.endpoint or f"mock://{self.engine}", "headers": {}, "log_headers": {}}
                endpoint = settings["endpoint"]

            try:
                response_payload, raw_bytes = self._dispatch(
                    endpoint,
                    request_payload,
                    headers=settings["headers"],
                    timeout=resolved_timeout,
                    prompt=prompt,
                    parameters=parameters,
                )
                if len(raw_bytes) > MAX_RESPONSE_BYTES:
                    raise ExternalRequestError(
                        "bad_response",
                        "response_body_exceeds_1MiB",
                        retryable=False,
                    )
                response_hash = hashlib.sha256(raw_bytes).hexdigest()[:16]
                attempt_record["status"] = "ok"
                attempt_record["response_meta"] = {
                    "hash": response_hash,
                    "size": len(raw_bytes),
                }
                attempts.append(attempt_record)

                asset = self._parse_response(
                    response_payload,
                    prompt,
                    parameters,
                    trace_id=run_trace_id,
                    mode="mock" if self.mock_mode else "live",
                    endpoint=endpoint,
                    response_hash=response_hash,
                    schema_version=resolved_schema_version,
                )

                context: JsonDict = {
                    "trace_id": run_trace_id,
                    "prompt": prompt,
                    "engine": self.engine,
                    "api_version": self.api_version,
                    "parameters": parameters,
                    "mode": "mock" if self.mock_mode else "live",
                    "attempts": attempts,
                    "request": request_payload,
                    "request_headers": settings["log_headers"],
                    "response_hash": response_hash,
                    "response_size": len(raw_bytes),
                    "asset_id": asset.get("asset_id"),
                    "generated_at": asset.get("timestamp")
                    or _dt.datetime.now(tz=_dt.timezone.utc).isoformat(),
                    "strict": strict_mode,
                    "endpoint": endpoint,
                    "raw_response": {
                        "hash": response_hash,
                        "size": len(raw_bytes),
                        "redacted": not self.mock_mode,
                    },
                    "asset": asset,
                    "schema_version": resolved_schema_version,
                    "taxonomy": f"external.{self.engine}",
                }
                return asset, context
            except ExternalRequestError as exc:
                attempts.append(
                    self._record_failure_attempt(attempt_record, exc.reason, exc.detail)
                )
                final_error = exc
                last_exception = exc
                if attempt == self.max_retries or not exc.retryable:
                    break
                self._sleep(self._compute_backoff(attempt))
            except Exception as exc:  # pragma: no cover - unexpected failure
                generic_error = ExternalRequestError(
                    "bad_response",
                    f"unexpected_error: {exc}",
                    retryable=False,
                )
                attempts.append(
                    self._record_failure_attempt(attempt_record, generic_error.reason, generic_error.detail)
                )
                final_error = generic_error
                last_exception = exc
                break

        assert final_error is not None
        trace = {
            "trace_id": run_trace_id,
            "prompt": prompt,
            "engine": self.engine,
            "api_version": self.api_version,
            "parameters": parameters,
            "mode": "mock" if self.mock_mode else "live",
            "attempts": attempts,
            "failure": {
                "reason": final_error.reason,
                "detail": final_error.detail,
            },
        }
        message = f"{self.engine} generation failed after {self.max_retries} attempts"
        raise ExternalGenerationError(
            message,
            trace=trace,
            reason=final_error.reason,
            detail=final_error.detail,
            cause=last_exception,
        )

    def record_run(
        self,
        *,
        context: JsonDict,
        review: JsonDict,
        experiment_path: Optional[str],
    ) -> None:
        """Persist a structured log entry for a successful API invocation."""

        status = "validation_passed" if review.get("ok") else "validation_failed"
        record: JsonDict = {
            "ts": _dt.datetime.now(tz=_dt.timezone.utc).isoformat(),
            "trace_id": context.get("trace_id"),
            "prompt": context.get("prompt"),
            "engine": self.engine,
            "mode": context.get("mode"),
            "strict": context.get("strict"),
            "transport": review.get("transport"),
            "parameters": context.get("parameters"),
            "request": context.get("request"),
            "request_headers": context.get("request_headers"),
            "raw_response": context.get("raw_response"),
            "normalized_asset": context.get("asset"),
            "mcp_result": review.get("mcp_response"),
            "provenance": context.get("asset", {}).get("meta_info", {}).get("provenance"),
            "asset_id": context.get("asset_id"),
            "generated_at": context.get("generated_at"),
            "experiment_path": experiment_path,
            "status": status,
            "schema_version": context.get("schema_version"),
            "$schema": context.get("asset", {}).get("$schema"),
            "taxonomy": context.get("taxonomy") or f"external.{self.engine}",
        }

        failure_payload: Optional[JsonDict]
        if review.get("ok"):
            failure_payload = None
        else:
            failure_payload = {
                "reason": review.get("validation_error", {}).get("reason", "validation_failed"),
                "detail": review.get("validation_error", {}).get("detail")
                or review.get("validation_reason")
                or review.get("issues"),
            }
        record["failure"] = failure_payload

        log_external_generation(record, path=self.log_path)

    def record_failure(self, error: ExternalGenerationError) -> None:
        """Log a failed invocation with its attempt trace."""

        trace = dict(error.trace)
        trace.update(
            {
                "ts": _dt.datetime.now(tz=_dt.timezone.utc).isoformat(),
                "status": "api_failed",
                "failure": {
                    "reason": error.reason,
                    "detail": error.detail,
                },
            }
        )
        log_external_generation(trace, path=self.log_path)

    # Hooks for subclasses -------------------------------------------------------
    def default_parameters(self) -> JsonDict:
        """Return default parameters merged into each request."""

        return {}

    def _request_envelope(self, prompt: str, parameters: JsonDict, trace_id: str) -> JsonDict:
        envelope: JsonDict = {
            "trace_id": trace_id,
            "prompt": prompt,
            "seed": parameters.get("seed"),
            "hints": {
                "need_sections": ["shader", "tone", "haptic", "control", "modulations", "meta_info"],
                "schema": "nested-synesthetic-asset@>=0.7.3",
                "strict_json": True,
            },
            "parameters": {
                "model": parameters.get("model"),
                "temperature": parameters.get("temperature"),
                "max_tokens": parameters.get("max_tokens"),
            },
        }
        if envelope["seed"] is None:
            envelope.pop("seed")
        return envelope

    def _build_request(
        self,
        envelope: JsonDict,
        prompt: str,
        parameters: JsonDict,
    ) -> JsonDict:
        return envelope

    def _dispatch(
        self,
        endpoint: str,
        payload: JsonDict,
        *,
        headers: Dict[str, str],
        timeout: float,
        prompt: str,
        parameters: JsonDict,
    ) -> Tuple[JsonDict, bytes]:
        if self.mock_mode:
            response = self._mock_response(prompt, parameters)
            raw_bytes = self._encode_payload(response)
            return response, raw_bytes

        if self._transport is not None:
            response = self._transport(payload)
            if not isinstance(response, dict):
                raise TypeError("transport must return a dictionary")
            raw_bytes = self._encode_payload(response)
            return response, raw_bytes

        return self._post_json(endpoint, payload, headers=headers, timeout=timeout)

    def _mock_response(self, prompt: str, parameters: JsonDict) -> JsonDict:  # pragma: no cover - abstract
        raise NotImplementedError

    def _parse_response(
        self,
        response: JsonDict,
        prompt: str,
        parameters: JsonDict,
        *,
        trace_id: str,
        mode: str,
        endpoint: str,
        response_hash: str,
        schema_version: str,
    ) -> JsonDict:  # pragma: no cover - abstract
        raise NotImplementedError

    # Helper methods -------------------------------------------------------------
    def _encode_payload(self, payload: JsonDict) -> bytes:
        return json.dumps(payload, sort_keys=True).encode("utf-8")

    def _record_failure_attempt(
        self,
        attempt_record: JsonDict,
        reason: str,
        detail: str,
    ) -> JsonDict:
        attempt_record = dict(attempt_record)
        attempt_record["status"] = "error"
        attempt_record["error"] = {"reason": reason, "detail": detail}
        return attempt_record

    def _compute_backoff(self, attempt: int) -> float:
        delay = min(
            self.backoff_seconds * (_BACKOFF_FACTOR ** (attempt - 1)),
            _BACKOFF_CAP_SECONDS,
        )
        jitter = random.uniform(0, delay * _JITTER_FRACTION)
        return delay + jitter

    def _resolve_live_settings(self) -> Dict[str, Any]:
        if not self.api_key_env:
            raise ExternalRequestError("auth_error", "api_key_env_not_configured", retryable=False)
        api_key = (os.getenv(self.api_key_env) or "").strip()
        if not api_key:
            raise ExternalRequestError("auth_error", "missing_api_key", retryable=False)

        endpoint = (os.getenv(self.endpoint_env or "") or self.default_endpoint or self.endpoint or "").strip()
        if not endpoint:
            raise ExternalRequestError("network_error", "missing_endpoint", retryable=False)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        log_headers = self._sanitize_headers_for_log(headers)
        return {"endpoint": endpoint, "headers": headers, "log_headers": log_headers}

    def _sanitize_headers_for_log(self, headers: Dict[str, str]) -> Dict[str, str]:
        sanitized: Dict[str, str] = {}
        for key, value in headers.items():
            if key.lower() in SENSITIVE_HEADERS:
                sanitized[key] = "***redacted***"
            else:
                sanitized[key] = value
        return sanitized

    def _post_json(
        self,
        endpoint: str,
        payload: JsonDict,
        *,
        headers: Dict[str, str],
        timeout: float,
    ) -> Tuple[JsonDict, bytes]:
        data = self._encode_payload(payload)
        if len(data) > MAX_REQUEST_BYTES:
            raise ExternalRequestError("bad_response", "request_body_exceeds_256KiB", retryable=False)

        request = urllib.request.Request(
            endpoint,
            data=data,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read(MAX_RESPONSE_BYTES + 1)
        except urllib.error.HTTPError as exc:
            reason, detail, retryable = self._classify_http_error(exc)
            raise ExternalRequestError(reason, detail, status_code=exc.code, retryable=retryable) from exc
        except urllib.error.URLError as exc:
            reason, detail = self._classify_url_error(exc)
            raise ExternalRequestError(reason, detail, retryable=reason not in {"auth_error", "bad_response"}) from exc
        except socket.timeout as exc:  # pragma: no cover - defensive
            raise ExternalRequestError("timeout", "socket_timeout", retryable=True) from exc

        if len(body) > MAX_RESPONSE_BYTES:
            raise ExternalRequestError("bad_response", "response_body_exceeds_1MiB", retryable=False)

        try:
            parsed = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ExternalRequestError("bad_response", f"invalid_json: {exc}", retryable=False) from exc

        if not isinstance(parsed, dict):
            raise ExternalRequestError("bad_response", "response_not_object", retryable=False)

        return parsed, body

    def _classify_http_error(self, error: urllib.error.HTTPError) -> Tuple[str, str, bool]:
        status = error.code
        detail = f"http_{status}"
        if status in {401, 403}:
            return "auth_error", detail, False
        if status == 429:
            return "rate_limited", detail, True
        if 500 <= status < 600:
            return "server_error", detail, True
        return "bad_response", detail, False

    def _classify_url_error(self, error: urllib.error.URLError) -> Tuple[str, str]:
        reason = error.reason
        if isinstance(reason, socket.timeout):
            return "timeout", "socket_timeout"
        text = str(reason)
        lowered = text.lower()
        if "timed out" in lowered:
            return "timeout", "request_timeout"
        return "network_error", text or "network_unavailable"

    def _normalise_asset(
        self,
        asset_payload: JsonDict,
        *,
        prompt: str,
        parameters: JsonDict,
        response: JsonDict,
        trace_id: str,
        mode: str,
        endpoint: str,
        response_hash: str,
        schema_version: str,
    ) -> JsonDict:
        self._logger.debug(
            "Normalizing asset payload: %s", json.dumps(asset_payload, indent=2)[:1000]
        )

        if isinstance(asset_payload, list):
            items = [item for item in asset_payload if isinstance(item, dict)]
            if items:
                self._logger.debug("Converting array response to single object")
                asset_payload = items[0]

        if not isinstance(asset_payload, dict):
            self._logger.error("Asset payload is not a dictionary: %s", type(asset_payload))
            raise ExternalRequestError("bad_response", "asset_not_object", retryable=False)

        for section in ("shader", "tone", "haptic"):
            if not isinstance(asset_payload.get(section), dict):
                self._logger.debug("Adding missing '%s' section", section)
                asset_payload[section] = {}

        if not isinstance(asset_payload.get("control"), dict):
            asset_payload["control"] = {}

        canonical = self._canonicalize_asset(asset_payload)
        self._validate_bounds(canonical)

        requested_schema_version = (
            schema_version
            or self.schema_version
            or AssetAssembler.DEFAULT_SCHEMA_VERSION
        )
        schema_url, resolved_schema_version, _schema_spec = _schema_descriptor(
            requested_schema_version
        )
        enriched_schema = self._supports_enriched_schema(resolved_schema_version)

        shader_section = self._merge_structured_section("shader", canonical.get("shader"))
        tone_section = self._merge_structured_section("tone", canonical.get("tone"))
        haptic_section = self._merge_structured_section("haptic", canonical.get("haptic"))

        parameter_index = self._collect_parameters(
            {
                "shader": shader_section,
                "tone": tone_section,
                "haptic": haptic_section,
            }
        )

        control_section = self._build_control_section(
            canonical.get("control"),
            canonical.get("controls"),
            parameter_index,
        )

        modulations = self._normalise_modulations(
            canonical.get("modulations"),
            canonical.get("modulation"),
        )
        if not modulations:
            modulations = deepcopy(_DEFAULT_MODULATIONS)

        rule_bundle = self._build_rule_bundle(canonical.get("rule_bundle"))
        rule_bundle_version = (
            rule_bundle.get("meta_info", {}).get("version", self.api_version)
        )

        timestamp: Optional[str]
        existing_timestamp = canonical.get("timestamp")
        timestamp = existing_timestamp if isinstance(existing_timestamp, str) else None
        if enriched_schema:
            timestamp = timestamp or _dt.datetime.now(tz=_dt.timezone.utc).isoformat()

        asset_id: Optional[str] = canonical.get("asset_id")
        if not isinstance(asset_id, str) or not asset_id.strip():
            asset_id = canonical.get("id")
        if not isinstance(asset_id, str) or not asset_id.strip():
            meta_asset_id = canonical.get("meta", {}).get("asset_id")  # type: ignore[arg-type]
            if isinstance(meta_asset_id, str) and meta_asset_id.strip():
                asset_id = meta_asset_id
        if enriched_schema and (not isinstance(asset_id, str) or not asset_id.strip()):
            asset_id = str(uuid.uuid4())

        sanitized_parameters = {
            key: deepcopy(value)
            for key, value in parameters.items()
            if value is not None
        }

        meta_info = self._build_meta_info(
            canonical.get("meta"),
            canonical.get("meta_info"),
            timestamp=timestamp,
            seed=parameters.get("seed"),
            trace_id=trace_id,
            endpoint=endpoint,
            parameters=parameters,
            mode=mode,
            response_hash=response_hash,
            include_provenance=enriched_schema,
        )
        if not isinstance(meta_info, dict):
            meta_info = {}

        provenance_block: Optional[Dict[str, Any]] = None
        if enriched_schema and isinstance(timestamp, str):
            existing_provenance = canonical.get("provenance")
            if not isinstance(existing_provenance, dict):
                existing_provenance = None

            provenance_block = self._make_provenance_block(
                asset_id=asset_id,
                parameters=parameters,
                trace_id=trace_id,
                mode=mode,
                endpoint=endpoint,
                response=response,
                timestamp=timestamp,
                input_parameters={
                    "prompt": prompt,
                    "parameters": sanitized_parameters,
                    "taxonomy": {
                        "domain": "visual",
                        "task": "generation",
                        "style": (
                            "square" if "square" in prompt.lower() else "compositional"
                        ),
                    },
                },
                existing=existing_provenance,
            )
            meta_info.setdefault("provenance", {})
            meta_info["provenance"] = self._deep_merge_dicts(
                meta_info.get("provenance", {}), provenance_block
            )

        if not enriched_schema:
            legacy_asset: JsonDict = {
                "$schema": schema_url,
                "shader": shader_section,
                "tone": tone_section,
                "haptic": haptic_section,
                "control": control_section,
                "modulations": modulations,
                "rule_bundle": rule_bundle,
                "meta_info": meta_info,
            }
            return AssetAssembler._normalize_0_7_3(
                legacy_asset,
                prompt,
                rule_bundle_version,
            )

        enriched_asset: JsonDict = {
            "$schema": schema_url,
            "asset_id": asset_id,
            "prompt": prompt,
            "seed": parameters.get("seed"),
            "timestamp": timestamp,
            "shader": shader_section,
            "tone": tone_section,
            "haptic": haptic_section,
            "control": control_section,
            "modulations": modulations,
            "rule_bundle": rule_bundle,
            "meta_info": meta_info,
        }

        enriched_asset["parameter_index"] = sorted(parameter_index)

        return AssetAssembler._normalize_0_7_4(
            enriched_asset,
            prompt,
            asset_id if isinstance(asset_id, str) else str(uuid.uuid4()),
            timestamp if isinstance(timestamp, str) else _dt.datetime.now(tz=_dt.timezone.utc).isoformat(),
            parameter_index,
            provenance_block or {},
            rule_bundle_version,
        )

    @staticmethod
    def _supports_enriched_schema(schema_version: Optional[str]) -> bool:
        if not schema_version:
            return False
        try:
            parts = tuple(int(part) for part in str(schema_version).split("."))
        except ValueError:
            return str(schema_version) >= "0.7.4"
        return parts >= (0, 7, 4)

    def _canonicalize_asset(self, payload: JsonDict) -> JsonDict:
        if not isinstance(payload, dict):
            raise ExternalRequestError("bad_response", "asset_not_object", retryable=False)

        allowed_keys = {
            "$schema",
            "asset_id",
            "id",
            "name",
            "prompt",
            "timestamp",
            "shader",
            "tone",
            "haptic",
            "control",
            "controls",
            "meta",
            "meta_info",
            "modulation",
            "modulations",
            "rule_bundle",
            "parameter_index",
            "seed",
            "provenance",
        }
        unexpected = sorted(key for key in payload.keys() if key not in allowed_keys)
        if unexpected:
            raise ExternalRequestError(
                "bad_response",
                f"unknown_key:{unexpected[0]}",
                retryable=False,
            )

        sanitized: JsonDict = {}

        for key in ("asset_id", "id", "prompt", "timestamp", "seed", "provenance"):
            if key in payload:
                sanitized[key] = deepcopy(payload[key])

        map_sections = {
            "shader": dict,
            "tone": dict,
            "haptic": dict,
            "control": dict,
            "meta": dict,
            "meta_info": dict,
            "modulation": dict,
            "rule_bundle": dict,
        }

        for section, expected_type in map_sections.items():
            if section in payload:
                section_payload = payload[section]
                if not isinstance(section_payload, expected_type):
                    raise ExternalRequestError(
                        "bad_response",
                        f"wrong_type:{section}",
                        retryable=False,
                    )
                sanitized[section] = deepcopy(section_payload)

        if "modulations" in payload:
            modulations = payload["modulations"]
            if not isinstance(modulations, list):
                raise ExternalRequestError("bad_response", "wrong_type:modulations", retryable=False)
            if not all(isinstance(item, dict) for item in modulations):
                raise ExternalRequestError("bad_response", "wrong_type:modulations[]", retryable=False)
            sanitized["modulations"] = deepcopy(modulations)

        if "controls" in payload:
            controls = payload["controls"]
            if controls is None:
                sanitized["controls"] = None
            elif not isinstance(controls, list) or not all(isinstance(item, dict) for item in controls):
                raise ExternalRequestError("bad_response", "wrong_type:controls", retryable=False)
            else:
                sanitized["controls"] = deepcopy(controls)

        if "parameter_index" in payload:
            parameter_index = payload["parameter_index"]
            if not isinstance(parameter_index, list) or not all(
                isinstance(entry, str) for entry in parameter_index
            ):
                raise ExternalRequestError(
                    "bad_response",
                    "wrong_type:parameter_index",
                    retryable=False,
                )
            sanitized["parameter_index"] = list(parameter_index)

        return sanitized


    def _validate_bounds(self, asset: JsonDict) -> None:
        def _fail(detail: str) -> None:
            raise ExternalRequestError("bad_response", detail, retryable=False)

        def _as_number(value: Any, path: str) -> float:
            if isinstance(value, bool) or not isinstance(value, Real):
                _fail(f"wrong_type:{path}")
            return float(value)

        haptic = asset.get("haptic", {})
        if not isinstance(haptic, dict):
            _fail("wrong_type:haptic")
        profile = haptic.get("profile")
        if isinstance(profile, dict) and "intensity" in profile:
            intensity = _as_number(profile["intensity"], "haptic.profile.intensity")
            if not 0.0 <= intensity <= 1.0:
                _fail("out_of_range:haptic.profile.intensity")

        for section_key in ("shader", "tone", "haptic"):
            section = asset.get(section_key, {})
            if not isinstance(section, dict):
                _fail(f"wrong_type:{section_key}")
            input_parameters = section.get("input_parameters")
            if input_parameters is None:
                continue
            if not isinstance(input_parameters, list):
                _fail(f"wrong_type:{section_key}.input_parameters")
            for index, parameter in enumerate(input_parameters):
                if not isinstance(parameter, dict):
                    _fail(f"wrong_type:{section_key}.input_parameters[{index}]")
                name = parameter.get("parameter")
                param_path = (
                    f"{section_key}.input_parameters.{name}"
                    if isinstance(name, str) and name
                    else f"{section_key}.input_parameters[{index}]"
                )
                minimum = parameter.get("minimum")
                maximum = parameter.get("maximum")
                default = parameter.get("default")

                min_value = None
                max_value = None

                if minimum is not None:
                    min_value = _as_number(minimum, f"{param_path}.minimum")
                if maximum is not None:
                    max_value = _as_number(maximum, f"{param_path}.maximum")

                if min_value is not None and max_value is not None and min_value > max_value:
                    _fail(f"invalid_bounds:{param_path}")

                if default is not None:
                    default_value = _as_number(default, f"{param_path}.default")
                    if min_value is not None and default_value < min_value:
                        _fail(f"out_of_range:{param_path}.default")
                    if max_value is not None and default_value > max_value:
                        _fail(f"out_of_range:{param_path}.default")

    def _collect_parameters(self, sections: JsonDict) -> List[str]:
        parameters: List[str] = []
        for section_key in ("shader", "tone", "haptic"):
            section = sections.get(section_key, {})
            input_parameters = []
            if isinstance(section, dict):
                input_parameters = section.get("input_parameters", [])  # type: ignore[assignment]
            for entry in input_parameters:
                if not isinstance(entry, dict):
                    continue
                parameter = entry.get("parameter")
                if isinstance(parameter, str) and parameter not in parameters:
                    parameters.append(parameter)
        if not parameters:
            parameters.extend(_DEFAULT_PARAMETER_INDEX)
        return parameters

    def _build_control_section(
        self,
        control_payload: Any,
        legacy_controls: Any,
        parameter_index: List[str],
    ) -> Dict[str, Any]:
        base = deepcopy(_DEFAULT_SECTIONS["control"])
        control_parameters = []
        mappings: List[Dict[str, Any]] = []
        if isinstance(control_payload, dict):
            candidate = control_payload.get("mappings")
            if isinstance(candidate, list):
                mappings = [item for item in candidate if isinstance(item, dict)]
            meta_info = control_payload.get("meta_info")
            if isinstance(meta_info, dict):
                base.setdefault("meta_info", {}).update(deepcopy(meta_info))
            description = control_payload.get("description")
            if isinstance(description, str):
                base["description"] = description

        if isinstance(legacy_controls, list) and not mappings:
            mappings = [item for item in legacy_controls if isinstance(item, dict)]

        control_parameters = self._build_control_parameters(mappings, parameter_index)
        if not control_parameters:
            control_parameters = deepcopy(_DEFAULT_CONTROL_PARAMETERS)

        base["control_parameters"] = control_parameters
        return base

    def _build_control_parameters(
        self,
        mappings: List[Dict[str, Any]],
        parameter_index: List[str],
    ) -> List[Dict[str, Any]]:
        parameters: List[Dict[str, Any]] = []
        required_pairs = {
            ("mouse", "x", "shader.u_px"),
            ("mouse", "y", "shader.u_py"),
        }
        for mapping in mappings:
            parameter = mapping.get("parameter")
            if parameter not in parameter_index:
                continue
            control_input = mapping.get("input")
            device = None
            axis = None
            if isinstance(control_input, dict):
                device = control_input.get("device")
                axis = control_input.get("control")
            pair = (device, axis, parameter)
            if device and axis:
                required_pairs.discard((device, axis, parameter))
            parameters.append(
                {
                    "id": mapping.get("id") or parameter.replace(".", "_"),
                    "parameter": parameter,
                    "label": self._derive_control_label(device, axis, parameter),
                    "unit": self._derive_control_unit(parameter),
                    "sensitivity": mapping.get("sensitivity", 1.0),
                    "combo": [
                        {
                            "device": device,
                            "control": axis,
                        }
                    ],
                    "mode": mapping.get("mode", "absolute"),
                    "curve": mapping.get("curve", "linear"),
                    "range": deepcopy(mapping.get("range")) if isinstance(mapping.get("range"), dict) else None,
                    "invert": mapping.get("invert"),
                }
            )

        # Remove None values for range/invert to keep payload tidy
        for entry in parameters:
            if entry.get("range") is None:
                entry.pop("range", None)
            if entry.get("invert") is None:
                entry.pop("invert", None)

        if required_pairs:
            default_lookup = {
                item["parameter"]: item for item in _DEFAULT_CONTROL_PARAMETERS if isinstance(item, dict)
            }
            for device, axis, parameter in required_pairs:
                default_entry = deepcopy(default_lookup.get(parameter, {}))
                if not default_entry:
                    default_entry = {
                        "id": parameter.replace(".", "_"),
                        "parameter": parameter,
                        "label": self._derive_control_label(device, axis, parameter),
                        "unit": self._derive_control_unit(parameter),
                        "sensitivity": 1.0,
                        "combo": [
                            {
                                "device": device,
                                "control": axis,
                            }
                        ],
                        "mode": "absolute",
                        "curve": "linear",
                        "range": {"minimum": -1.0, "maximum": 1.0},
                    }
                parameters.append(default_entry)

        return parameters

    def _normalise_modulations(
        self,
        modulations: Any,
        modulation_block: Any,
    ) -> List[Dict[str, Any]]:
        if isinstance(modulations, list):
            return [deepcopy(item) for item in modulations if isinstance(item, dict)]
        if isinstance(modulation_block, dict):
            candidate = modulation_block.get("modulators")
            if isinstance(candidate, list):
                return [deepcopy(item) for item in candidate if isinstance(item, dict)]
        return []

    @staticmethod
    def _derive_control_label(
        device: Optional[str], axis: Optional[str], parameter: str
    ) -> str:
        if device and axis:
            return f"{device}.{axis}"
        return parameter

    @staticmethod
    def _derive_control_unit(parameter: str) -> str:
        if parameter.startswith("shader."):
            return "normalized"
        if parameter.startswith("tone."):
            return "audio"
        if parameter.startswith("haptic."):
            return "haptic"
        return "generic"

    def _build_rule_bundle(self, payload: Any) -> Dict[str, Any]:
        base = deepcopy(_DEFAULT_SECTIONS["rule_bundle"])
        if isinstance(payload, dict):
            base = self._deep_merge_dicts(base, payload)
        if not isinstance(base.get("rules"), list):
            base["rules"] = []

        meta_info = base.get("meta_info")
        if not isinstance(meta_info, dict):
            meta_info = {}
        meta_info.setdefault("version", self.api_version)
        base["meta_info"] = meta_info

        name = base.get("name")
        if not isinstance(name, str) or not name.strip():
            base["name"] = f"{self.engine.title()} Rule Bundle"
        return base

    def _build_meta_info(
        self,
        meta_payload: Any,
        meta_info_payload: Any,
        *,
        timestamp: Optional[str],
        seed: Optional[int],
        trace_id: Optional[str],
        endpoint: str,
        parameters: JsonDict,
        mode: str,
        response_hash: str,
        include_provenance: bool,
    ) -> Dict[str, Any]:
        base = deepcopy(_DEFAULT_SECTIONS["meta_info"])
        for source in (meta_payload, meta_info_payload):
            if isinstance(source, dict):
                base = self._deep_merge_dicts(base, source)

        tags = base.get("tags")
        if not isinstance(tags, list):
            base["tags"] = [self.engine, "external"]
        elif self.engine not in tags:
            base["tags"].append(self.engine)

        base.setdefault("title", f"{self.engine.title()} synesthetic asset")
        base.setdefault("description", "Generated via external engine normalization")
        base.setdefault("category", "multimodal")
        base.setdefault("complexity", "baseline")

        if include_provenance:
            existing = base.get("provenance") if isinstance(base.get("provenance"), dict) else {}
            provenance_block: Dict[str, Any] = {
                "engine": self.engine,
                "endpoint": endpoint,
                "model": parameters.get("model"),
                "parameters": {
                    "temperature": parameters.get("temperature"),
                    "seed": seed,
                },
                "trace_id": trace_id,
                "mode": mode,
                "timestamp": timestamp,
                "response_hash": response_hash,
            }
            base["provenance"] = self._deep_merge_dicts(existing, provenance_block)
        else:
            base.pop("provenance", None)
        return base

    def _make_provenance_block(
        self,
        *,
        asset_id: str,
        parameters: JsonDict,
        trace_id: str,
        mode: str,
        endpoint: str,
        response: JsonDict,
        timestamp: str,
        input_parameters: Optional[Dict[str, Any]] = None,
        existing: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        provenance = {
            "agent": "ExternalGenerator",
            "version": self.api_version,
            "seed": parameters.get("seed"),
            "assembled_at": timestamp,
            "asset_id": asset_id,
            "generator": {
                "class": self.__class__.__name__,
                "engine": self.engine,
                "api_version": self.api_version,
                "trace_id": trace_id,
                "mode": mode,
                "endpoint": endpoint,
                "response_id": response.get("id"),
            },
        }
        if input_parameters is not None:
            provenance["input_parameters"] = input_parameters
        if existing:
            provenance = self._deep_merge_dicts(existing, provenance)
        return provenance

    def _deep_merge_dicts(self, base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
        merged = deepcopy(base)
        for key, value in overrides.items():
            if key not in merged:
                merged[key] = deepcopy(value)
                continue
            if isinstance(merged.get(key), dict) and isinstance(value, dict):
                merged[key] = self._deep_merge_dicts(merged[key], value)
            else:
                merged[key] = deepcopy(value)
        return merged

    def _merge_structured_section(self, section: str, payload: Any) -> Dict[str, Any]:
        base = deepcopy(_DEFAULT_SECTIONS[section])
        if isinstance(payload, dict):
            base = self._deep_merge_dicts(base, payload)
        return base


class GeminiGenerator(ExternalGenerator):
    """Google Gemini generator (v1beta generateContent)."""

    engine = "gemini"
    api_version = "v1beta"

    api_key_env = "GEMINI_API_KEY"
    endpoint_env = "GEMINI_ENDPOINT"
    default_model = "gemini-2.0-flash"
    
    @property
    def default_endpoint(self) -> str:
        """Dynamically build endpoint URL with model from env vars."""
        model = os.getenv("GEMINI_MODEL", self.default_model)
        return f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    @staticmethod
    def _redact_endpoint(endpoint: str) -> str:
        if not endpoint:
            return endpoint
        parsed = urlparse(endpoint)
        redacted = False
        redacted_query = []
        for key, value in parse_qsl(parsed.query, keep_blank_values=True):
            if key.lower() == "key":
                redacted = True
                redacted_query.append((key, "***redacted***"))
            else:
                redacted_query.append((key, value))
        if redacted:
            parsed = parsed._replace(query=urlencode(redacted_query))
            return urlunparse(parsed)
        return endpoint

    def _build_live_headers(self, api_key: str) -> Tuple[Dict[str, str], Dict[str, str]]:
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
        }
        return headers, self._sanitize_headers_for_log(headers)

    def _build_request_endpoint(self, endpoint: str, api_key: str) -> str:
        parsed = urlparse(endpoint)
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query["key"] = api_key
        return urlunparse(parsed._replace(query=urlencode(query)))

    def connectivity_check(
        self,
        *,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 5.0,
    ) -> None:
        """Ensure Gemini endpoint and credentials are available before live requests."""

        if (
            self.mock_mode
            or self._transport is not None
            or getattr(self, "_connectivity_checked", False)
        ):
            return

        resolved_endpoint = (
            (endpoint or os.getenv(self.endpoint_env or "") or self.default_endpoint or getattr(self, "endpoint", None) or "").strip()
        )
        resolved_api_key = (api_key or os.getenv(self.api_key_env or "") or "").strip()

        if not resolved_api_key:
            raise ExternalRequestError(
                "connectivity_check_failed",
                "missing_api_key",
                retryable=False,
            )

        if not resolved_endpoint:
            raise ExternalRequestError(
                "connectivity_check_failed",
                "missing_endpoint",
                retryable=False,
            )

        request_headers = headers or self._build_live_headers(resolved_api_key)[0]
        request_endpoint = self._build_request_endpoint(resolved_endpoint, resolved_api_key)
        payload = self._build_request({}, "ping", {})

        try:
            self._logger.debug("Gemini sending payload: %s", json.dumps(payload, indent=2))
            response = requests.post(request_endpoint, json=payload, headers=request_headers, timeout=timeout)
            self._logger.debug("Gemini response status: %s", response.status_code)
            if response.status_code >= 400:
                self._logger.debug("Gemini error response body: %s", response.text)
        except requests.RequestException as exc:
            self._logger.warning("Gemini connectivity probe failed for %s: %s", resolved_endpoint, exc)
            raise ExternalRequestError(
                "connectivity_check_failed",
                "endpoint_unreachable",
                retryable=False,
            ) from exc

        if not (200 <= response.status_code < 300):
            self._logger.warning(
                "Gemini connectivity check returned %s for %s", response.status_code, resolved_endpoint
            )
            raise ExternalRequestError(
                "connectivity_check_failed",
                f"unexpected_status_{response.status_code}",
                retryable=False,
            )

        self._connectivity_checked = True

    def _resolve_live_settings(self) -> Dict[str, Any]:
        api_key = (os.getenv(self.api_key_env or "") or "").strip()
        if not api_key:
            raise ExternalRequestError("auth_error", "missing_api_key", retryable=False)

        endpoint = (os.getenv(self.endpoint_env or "") or self.default_endpoint or getattr(self, "endpoint", None) or "").strip()
        if not endpoint:
            raise ExternalRequestError("network_error", "missing_endpoint", retryable=False)

        headers, log_headers = self._build_live_headers(api_key)
        request_endpoint = self._build_request_endpoint(endpoint, api_key)
        self._gemini_request_endpoint = request_endpoint
        self.connectivity_check(endpoint=endpoint, api_key=api_key, headers=headers)
        return {"endpoint": endpoint, "headers": headers, "log_headers": log_headers}

    def _dispatch(
        self,
        endpoint: str,
        payload: JsonDict,
        *,
        headers: Dict[str, str],
        timeout: float,
        prompt: str,
        parameters: JsonDict,
    ) -> Tuple[JsonDict, bytes]:
        request_endpoint = getattr(self, "_gemini_request_endpoint", endpoint)
        sanitized_endpoint = self._redact_endpoint(request_endpoint)
        self._logger.debug("Gemini actual generation endpoint: %s", sanitized_endpoint)
        self._logger.debug("Gemini actual generation payload: %s", json.dumps(payload, indent=2))
        return super()._dispatch(
            request_endpoint,
            payload,
            headers=headers,
            timeout=timeout,
            prompt=prompt,
            parameters=parameters,
        )

    def default_parameters(self) -> JsonDict:
        return {
            "model": os.getenv("GEMINI_MODEL", self.default_model),
            "temperature": None,
        }

    def _build_request(self, envelope: JsonDict, prompt: str, parameters: JsonDict) -> JsonDict:
        payload: JsonDict = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt},
                    ],
                }
            ],
            "generationConfig": {"responseMimeType": "application/json"},
            "model": parameters.get("model") or os.getenv("GEMINI_MODEL", self.default_model),
        }

        generation_config: JsonDict = payload["generationConfig"]
        temperature = parameters.get("temperature")
        if isinstance(temperature, Real):
            generation_config["temperature"] = float(temperature)

        max_tokens = parameters.get("max_tokens")
        if isinstance(max_tokens, int) and max_tokens > 0:
            generation_config["maxOutputTokens"] = max_tokens

        seed = parameters.get("seed")
        if isinstance(seed, int):
            generation_config["seed"] = seed

        return payload

    def _mock_response(self, prompt: str, parameters: JsonDict) -> JsonDict:
        # Create a complete valid asset using the assembler
        schema_version = parameters.get("schema_version", "0.7.3")
        assembler = AssetAssembler(schema_version=schema_version)
        baseline_asset = assembler.generate(
            f"{prompt}", 
            seed=parameters.get("seed", 42), 
            schema_version=schema_version
        )
        
        # Add Gemini-specific metadata
        baseline_asset["name"] = "Square Harmony Asset"
        if "meta_info" not in baseline_asset:
            baseline_asset["meta_info"] = {}
        if "tags" not in baseline_asset["meta_info"]:
            baseline_asset["meta_info"]["tags"] = []
        baseline_asset["meta_info"]["tags"].extend(["external", "gemini", "mock"])
        
        timestamp = _dt.datetime.now(tz=_dt.timezone.utc).isoformat()
        baseline_asset["timestamp"] = timestamp
        
        # Handle provenance based on schema version
        if schema_version == "0.7.3":
            # For 0.7.3, provenance is a top-level property
            baseline_asset["provenance"] = {
                "generator": {
                    "engine": self.engine,
                    "endpoint": f"mock://{self.engine}",
                    "model": os.getenv("GEMINI_MODEL", self.default_model),
                    "parameters": {
                        "temperature": parameters.get("temperature"),
                        "seed": parameters.get("seed"),
                    },
                    "trace_id": str(uuid.uuid4()),
                    "mode": "mock",
                    "timestamp": timestamp,
                    "response_hash": "mock-response-hash"
                }
            }
            
            # Ensure parameter_index is present for 0.7.3
            if "parameter_index" not in baseline_asset:
                baseline_asset["parameter_index"] = []
        else:
            # For 0.7.4+, provenance goes in meta_info
            if "provenance" not in baseline_asset["meta_info"]:
                baseline_asset["meta_info"]["provenance"] = {}
                
            baseline_asset["meta_info"]["provenance"].update({
                "engine": self.engine,
                "endpoint": f"mock://{self.engine}",
                "model": os.getenv("GEMINI_MODEL", self.default_model),
                "parameters": {
                    "temperature": parameters.get("temperature"),
                    "seed": parameters.get("seed"),
                },
                "trace_id": str(uuid.uuid4()),
                "mode": "mock",
                "timestamp": timestamp,
                "response_hash": "mock-response-hash",
                "input_parameters": {
                    "prompt": prompt,
                    "parameters": parameters,
                    "taxonomy": {
                        "domain": "visual",
                        "task": "generation",
                        "style": "square" if "square" in prompt.lower() else "compositional"
                    }
                }
            })
        
        # Return asset directly instead of nesting
        return baseline_asset

    def _parse_response(
        self,
        response: JsonDict,
        prompt: str,
        parameters: JsonDict,
        *,
        trace_id: str,
        mode: str,
        endpoint: str,
        response_hash: str,
        schema_version: str,
    ) -> JsonDict:
        """Parse and normalize a Gemini response into a valid synesthetic asset."""
        _, resolved_schema_version, schema_spec = _schema_descriptor(schema_version)

        # Mock responses may already supply an asset payload
        if isinstance(response, dict) and "candidates" not in response:
            return self._normalise_asset(
                response,
                prompt=prompt,
                parameters=parameters,
                response=response,
                trace_id=trace_id,
                mode=mode,
                endpoint=endpoint,
                response_hash=response_hash,
                schema_version=resolved_schema_version,
            )

        asset_payload = _build_schema_skeleton(schema_spec)

        try:
            self._logger.debug(
                "Gemini parse_response received: %s", json.dumps(response, indent=2)
            )
            candidate = response["candidates"][0]
            content = candidate["content"]
            parts = content["parts"]
            text = parts[0]["text"]
            self._logger.debug("Gemini extracted text: %s", text[:500])

            gemini_data = json.loads(text)
            if isinstance(gemini_data, list) and gemini_data:
                gemini_data = gemini_data[0]

            if isinstance(gemini_data, dict):
                if gemini_data.get("name"):
                    asset_payload["name"] = gemini_data["name"]

                if (
                    gemini_data.get("description")
                    and isinstance(asset_payload.get("shader"), dict)
                ):
                    asset_payload["shader"]["description"] = gemini_data["description"]

                shader_defs = gemini_data.get("shader_definitions")
                if isinstance(shader_defs, list):
                    shader_section = asset_payload.get("shader")
                    if isinstance(shader_section, dict):
                        shader_section.setdefault("sources", {})
                        for shader_def in shader_defs:
                            if not isinstance(shader_def, dict):
                                continue
                            square_code = shader_def.get("code", "")
                            if square_code and "squareSDF" in square_code:
                                shader_section["name"] = shader_def.get("name", "SquareSDF")
                                shader_section["sources"]["fragment"] = square_code
                                self._logger.debug("Updated shader with squareSDF implementation")

                meta_info = asset_payload.setdefault("meta_info", {})
                tags = meta_info.get("tags")
                if not isinstance(tags, list):
                    tags = []
                if "square" in prompt.lower():
                    tags.extend(["external", "gemini", "square"])
                else:
                    tags.extend(["external", "gemini"])
                meta_info["tags"] = list(dict.fromkeys(tags))
                meta_info["gemini_response"] = gemini_data

        except Exception as exc:  # pragma: no cover - defensive fallback
            self._logger.error("Error processing Gemini response: %s", exc)
            fallback_asset = _build_schema_skeleton(schema_spec)
            meta_info = fallback_asset.setdefault("meta_info", {})
            meta_info["fallback"] = True
            meta_info["raw_response"] = str(response)[:1000]
            asset_payload = fallback_asset

        return self._normalise_asset(
            asset_payload,
            prompt=prompt,
            parameters=parameters,
            response=response,
            trace_id=trace_id,
            mode=mode,
            endpoint=endpoint,
            response_hash=response_hash,
            schema_version=resolved_schema_version,
        )


class OpenAIGenerator(ExternalGenerator):
    engine = "openai"
    api_version = "v1"

    api_key_env = "OPENAI_API_KEY"
    endpoint_env = "OPENAI_ENDPOINT"
    default_endpoint = "https://api.openai.com/v1/chat/completions"

    def default_parameters(self) -> JsonDict:
        return {
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "temperature": float(os.getenv("OPENAI_TEMPERATURE", "0.4")),
        }

    def _build_request(self, envelope: JsonDict, prompt: str, parameters: JsonDict) -> JsonDict:
        return {
            "trace_id": envelope["trace_id"],
            "model": parameters.get("model"),
            "temperature": parameters.get("temperature"),
            "messages": [
                {"role": "system", "content": "You are a Synesthetic asset generator."},
                {"role": "user", "content": prompt},
            ],
        }

    def _mock_response(self, prompt: str, parameters: JsonDict) -> JsonDict:
        timestamp = _dt.datetime.now(tz=_dt.timezone.utc).isoformat()
        default_mappings = []
        for entry in _DEFAULT_CONTROL_PARAMETERS:
            if not isinstance(entry, dict):
                continue
            combo_list = entry.get("combo")
            combo = combo_list[0] if isinstance(combo_list, list) and combo_list else {}
            if not isinstance(combo, dict):
                combo = {}
            mapping = {
                "id": entry.get("id"),
                "input": {
                    "device": combo.get("device"),
                    "control": combo.get("control"),
                },
                "parameter": entry.get("parameter"),
                "mode": entry.get("mode", "absolute"),
                "curve": entry.get("curve", "linear"),
            }
            range_block = entry.get("range")
            if isinstance(range_block, dict):
                mapping["range"] = deepcopy(range_block)
            default_mappings.append(mapping)
        return {
            "id": f"openai-mock-{uuid.uuid4()}",
            "object": "synesthetic.asset",
            "asset": {
                "shader": {"component": "shader", "style": "prismatic", "prompt": prompt},
                "tone": {"component": "tone", "mood": "uplifting"},
                "haptic": {"component": "haptic", "pattern": "pulse"},
                "control": {"component": "control", "mappings": default_mappings},
                "meta": {"component": "meta", "tags": ["external", "openai"]},
                "modulations": [],
                "rule_bundle": {"component": "rule_bundle", "rules": []},
                "timestamp": timestamp,
            },
        }

    def _parse_response(
        self,
        response: JsonDict,
        prompt: str,
        parameters: JsonDict,
        *,
        trace_id: str,
        mode: str,
        endpoint: str,
        response_hash: str,
        schema_version: str,
    ) -> JsonDict:
        asset_payload = response.get("asset")
        if not isinstance(asset_payload, dict):
            raise ValueError("OpenAI response missing 'asset' payload")
        asset = self._normalise_asset(
            asset_payload,
            prompt=prompt,
            parameters=parameters,
            response=response,
            trace_id=trace_id,
            mode=mode,
            endpoint=endpoint,
            response_hash=response_hash,
            schema_version=schema_version,
        )
        provenance = dict(asset.get("provenance") or {})
        provenance["openai_object"] = response.get("object")
        asset["provenance"] = provenance
        return asset


def build_external_generator(engine: str, **kwargs: Any) -> ExternalGenerator:
    """Factory returning the configured external generator for *engine*."""

    normalised = engine.strip().lower()
    if normalised == "gemini":
        return GeminiGenerator(**kwargs)
    if normalised == "openai":
        return OpenAIGenerator(**kwargs)
    raise ValueError(f"unsupported external engine: {engine}")
