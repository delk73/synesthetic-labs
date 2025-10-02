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
import uuid
from copy import deepcopy
from typing import Any, Callable, Dict, List, Optional, Tuple

from labs.generator.assembler import AssetAssembler
from labs.logging import log_external_generation

JsonDict = Dict[str, Any]

MAX_REQUEST_BYTES = 256 * 1024
MAX_RESPONSE_BYTES = 1024 * 1024
_DEFAULT_BACKOFF_BASE_SECONDS = 0.2
_BACKOFF_FACTOR = 2.0
_BACKOFF_CAP_SECONDS = 5.0
_JITTER_FRACTION = 0.2

SENSITIVE_HEADERS = {"authorization"}

_BASELINE_ASSET = AssetAssembler().generate("external-normalization-baseline", seed=0)
_DEFAULT_SECTIONS = {
    key: deepcopy(_BASELINE_ASSET[key]) for key in ("shader", "tone", "haptic", "control", "meta", "modulation", "rule_bundle")
}
_DEFAULT_CONTROLS = deepcopy(_BASELINE_ASSET.get("controls", []))
_DEFAULT_PARAMETER_INDEX = list(_BASELINE_ASSET.get("parameter_index", []))


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

    # Public API -----------------------------------------------------------------
    def generate(
        self,
        prompt: str,
        *,
        parameters: Optional[JsonDict] = None,
        seed: Optional[int] = None,
        timeout: Optional[float] = None,
        trace_id: Optional[str] = None,
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
                    "asset_id": asset.get("id"),
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
            "provenance": context.get("asset", {}).get("meta", {}).get("provenance"),
            "asset_id": context.get("asset_id"),
            "generated_at": context.get("generated_at"),
            "experiment_path": experiment_path,
            "status": status,
        }

        if not review.get("ok"):
            record["failure"] = {
                "reason": review.get("validation_error", {}).get("reason", "validation_failed"),
                "detail": review.get("validation_error", {}).get("detail")
                or review.get("validation_reason")
                or review.get("issues"),
            }

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
                "need_sections": ["shader", "tone", "haptic", "controls", "meta"],
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
    ) -> JsonDict:
        if not isinstance(asset_payload, dict):
            raise ValueError("response missing 'asset' dictionary payload")

        asset = self._canonicalize_asset(asset_payload)

        timestamp = asset.get("timestamp") or _dt.datetime.now(tz=_dt.timezone.utc).isoformat()
        asset_id = asset.get("id") or asset.get("asset_id") or str(uuid.uuid4())
        asset["id"] = asset_id
        asset["prompt"] = prompt
        asset["timestamp"] = timestamp
        asset["seed"] = parameters.get("seed")

        parameter_index = self._collect_parameters(asset)
        mappings = self._sanitize_controls(asset, parameter_index)
        asset["controls"] = mappings
        asset.setdefault("control", {})["mappings"] = mappings
        asset["parameter_index"] = sorted(parameter_index)

        provenance_block = {
            "engine": self.engine,
            "api_endpoint": endpoint,
            "api_version": self.api_version,
            "model": parameters.get("model"),
            "parameters": {
                "temperature": parameters.get("temperature"),
                "seed": parameters.get("seed"),
            },
            "trace_id": trace_id,
            "mode": mode,
            "timestamp": timestamp,
        }

        meta = asset.setdefault("meta", {})
        defaults = deepcopy(_DEFAULT_SECTIONS["meta"])
        for key, value in defaults.items():
            meta.setdefault(key, value)
        meta.setdefault("category", "multimodal")
        meta.setdefault("complexity", "baseline")
        meta.setdefault("tags", defaults.get("tags", ["external", self.engine]))
        meta.setdefault("title", defaults.get("title", f"{self.engine.title()} synesthetic asset"))
        meta.setdefault("description", defaults.get("description", "Generated externally"))
        meta["provenance"] = provenance_block
        asset["meta"] = meta

        provenance = dict(asset.get("provenance") or {})
        provenance.setdefault("agent", "ExternalGenerator")
        provenance.setdefault("version", self.api_version)
        provenance["generator"] = {
            "agent": self.__class__.__name__,
            "engine": self.engine,
            "api_version": self.api_version,
            "parameters": parameters,
            "mode": mode,
            "trace_id": trace_id,
        }
        provenance["external_response_id"] = response.get("id")
        asset["provenance"] = provenance

        return asset

    def _canonicalize_asset(self, payload: JsonDict) -> JsonDict:
        allowed_keys = {
            "id",
            "prompt",
            "timestamp",
            "shader",
            "tone",
            "haptic",
            "control",
            "controls",
            "meta",
            "modulation",
            "rule_bundle",
            "parameter_index",
            "seed",
            "provenance",
        }
        sanitized: JsonDict = {}
        for key in allowed_keys:
            if key in payload:
                sanitized[key] = deepcopy(payload[key])
        for section in ("shader", "tone", "haptic", "control", "meta", "modulation", "rule_bundle"):
            if section not in sanitized or not isinstance(sanitized[section], dict):
                sanitized[section] = deepcopy(_DEFAULT_SECTIONS[section])
        return sanitized

    def _collect_parameters(self, asset: JsonDict) -> List[str]:
        parameters: List[str] = []
        for section_key in ("shader", "tone", "haptic"):
            section = asset.get(section_key, {})
            for entry in section.get("input_parameters", []):
                parameter = entry.get("parameter")
                if parameter and parameter not in parameters:
                    parameters.append(parameter)
        if not parameters:
            parameters.extend(_DEFAULT_PARAMETER_INDEX)
        return parameters

    def _sanitize_controls(self, asset: JsonDict, parameter_index: List[str]) -> List[JsonDict]:
        control_component = asset.get("control", {})
        mappings = control_component.get("mappings", []) if isinstance(control_component, dict) else []
        sanitized: List[JsonDict] = []
        required_mappings = {
            ("mouse.x", "shader.u_px"),
            ("mouse.y", "shader.u_py"),
        }
        for mapping in mappings:
            if not isinstance(mapping, dict):
                continue
            parameter = mapping.get("parameter")
            if parameter in parameter_index:
                sanitized.append(mapping)
                control = mapping.get("control")
                if control and parameter:
                    required_mappings.discard((control, parameter))
        if not sanitized:
            sanitized.extend(deepcopy(_DEFAULT_CONTROLS))
        for control, parameter in list(required_mappings):
            sanitized.append(
                {
                    "control": control,
                    "parameter": parameter,
                    "range": [-1.0, 1.0],
                }
            )
        return sanitized


class GeminiGenerator(ExternalGenerator):
    engine = "gemini"
    api_version = "v1beta"

    api_key_env = "GEMINI_API_KEY"
    endpoint_env = "GEMINI_ENDPOINT"
    default_endpoint = "https://generativelanguage.googleapis.com/v1beta/models/text:generate"

    def default_parameters(self) -> JsonDict:
        return {
            "model": os.getenv("GEMINI_MODEL", "gemini-pro"),
            "temperature": None,
        }

    def _build_request(self, envelope: JsonDict, prompt: str, parameters: JsonDict) -> JsonDict:
        payload = dict(envelope)
        payload.setdefault("parameters", {})
        return payload

    def _mock_response(self, prompt: str, parameters: JsonDict) -> JsonDict:
        timestamp = _dt.datetime.now(tz=_dt.timezone.utc).isoformat()
        return {
            "id": f"gemini-mock-{uuid.uuid4()}",
            "asset": {
                "shader": {"component": "shader", "style": "neon", "prompt": prompt},
                "tone": {"component": "tone", "mood": "serene"},
                "haptic": {"component": "haptic", "pattern": "soft"},
                "control": {"component": "control", "mappings": deepcopy(_DEFAULT_CONTROLS)},
                "meta": {"component": "meta", "tags": ["external", "gemini"]},
                "modulation": {"component": "modulation", "modulators": []},
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
    ) -> JsonDict:
        asset_payload = response.get("asset")
        if not isinstance(asset_payload, dict):
            raise ValueError("Gemini response missing 'asset' payload")
        return self._normalise_asset(
            asset_payload,
            prompt=prompt,
            parameters=parameters,
            response=response,
            trace_id=trace_id,
            mode=mode,
            endpoint=endpoint,
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
        return {
            "id": f"openai-mock-{uuid.uuid4()}",
            "object": "synesthetic.asset",
            "asset": {
                "shader": {"component": "shader", "style": "prismatic", "prompt": prompt},
                "tone": {"component": "tone", "mood": "uplifting"},
                "haptic": {"component": "haptic", "pattern": "pulse"},
                "control": {"component": "control", "mappings": deepcopy(_DEFAULT_CONTROLS)},
                "meta": {"component": "meta", "tags": ["external", "openai"]},
                "modulation": {"component": "modulation", "modulators": []},
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
