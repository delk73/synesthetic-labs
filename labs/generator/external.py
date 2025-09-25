"""External generator integrations for Synesthetic Labs."""

from __future__ import annotations

import datetime as _dt
import json
import logging
import os
import time
import uuid
from typing import Any, Callable, Dict, List, Optional, Tuple

from labs.logging import log_external_generation

JsonDict = Dict[str, Any]


class ExternalGenerationError(RuntimeError):
    """Raised when an external generator exhausts its retries."""

    def __init__(self, message: str, *, trace: JsonDict, cause: Optional[Exception] = None) -> None:
        super().__init__(message)
        self.trace = trace
        self.__cause__ = cause


class ExternalGenerator:
    """Base class for API-driven generators.

    Subclasses must supply ``engine`` and ``api_version`` attributes and
    implement the :meth:`_mock_response` and :meth:`_parse_response` hooks.
    """

    DEFAULT_LOG_PATH = "meta/output/labs/external.jsonl"
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_BACKOFF_SECONDS = 0.5
    DEFAULT_TIMEOUT_SECONDS = 15

    engine = "external"
    api_version = "unspecified"
    endpoint: Optional[str] = None

    def __init__(
        self,
        *,
        log_path: Optional[str] = None,
        transport: Optional[Callable[[JsonDict], JsonDict]] = None,
        mock_mode: Optional[bool] = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        if max_retries < 1:
            raise ValueError("max_retries must be >= 1")
        if backoff_seconds < 0:
            raise ValueError("backoff_seconds cannot be negative")
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
    ) -> Tuple[JsonDict, JsonDict]:
        """Return an asset assembled from an external API response.

        The second element of the tuple contains trace metadata that callers can
        persist via :meth:`record_run`.
        """

        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")

        parameters = dict(parameters or {})
        parameters.update({k: v for k, v in self.default_parameters().items() if k not in parameters})

        attempts: List[JsonDict] = []
        trace_id = str(uuid.uuid4())
        last_error: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            request_payload = self._build_request(prompt, parameters)
            attempt_record: JsonDict = {
                "attempt": attempt,
                "request": request_payload,
            }
            try:
                response_payload = self._dispatch(request_payload, prompt, parameters)
                attempt_record["response"] = response_payload
                asset = self._parse_response(
                    response_payload,
                    prompt,
                    parameters,
                    trace_id=trace_id,
                )
                attempt_record["status"] = "ok"
                attempts.append(attempt_record)

                context: JsonDict = {
                    "trace_id": trace_id,
                    "prompt": prompt,
                    "engine": self.engine,
                    "api_version": self.api_version,
                    "parameters": parameters,
                    "mode": "mock" if self.mock_mode else "live",
                    "attempts": attempts,
                    "request": request_payload,
                    "response": response_payload,
                    "asset_id": asset.get("id"),
                    "generated_at": asset.get("timestamp")
                    or _dt.datetime.now(tz=_dt.timezone.utc).isoformat(),
                }
                context["asset"] = asset
                return asset, context
            except Exception as exc:  # pragma: no cover - retry path exercised via tests
                attempt_record["status"] = "error"
                attempt_record["error"] = str(exc)
                attempts.append(attempt_record)
                last_error = exc
                self._logger.warning(
                    "External %s generation attempt %s failed: %s",
                    self.engine,
                    attempt,
                    exc,
                )
                if attempt < self.max_retries:
                    delay = self.backoff_seconds * attempt
                    if delay > 0:
                        self._sleep(delay)

        trace = {
            "trace_id": trace_id,
            "prompt": prompt,
            "engine": self.engine,
            "api_version": self.api_version,
            "parameters": parameters,
            "mode": "mock" if self.mock_mode else "live",
            "attempts": attempts,
        }
        message = f"{self.engine} generation failed after {self.max_retries} attempts"
        raise ExternalGenerationError(message, trace=trace, cause=last_error)

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
            "trace_id": context.get("trace_id"),
            "prompt": context.get("prompt"),
            "engine": self.engine,
            "api_version": self.api_version,
            "mode": context.get("mode"),
            "parameters": context.get("parameters"),
            "attempts": context.get("attempts"),
            "request": context.get("request"),
            "response": context.get("response"),
            "asset": context.get("asset"),
            "asset_id": context.get("asset_id"),
            "generated_at": context.get("generated_at"),
            "review": review,
            "mcp_result": review.get("mcp_response"),
            "experiment_path": experiment_path,
            "status": status,
            "logged_at": _dt.datetime.now(tz=_dt.timezone.utc).isoformat(),
        }

        if not review.get("ok"):
            record["failure"] = {
                "reason": "validation_failed",
                "detail": review.get("validation_reason") or review.get("issues"),
            }

        log_external_generation(record, path=self.log_path)

    def record_failure(self, error: ExternalGenerationError) -> None:
        """Log a failed invocation with its attempt trace."""

        trace = dict(error.trace)
        trace.update(
            {
                "status": "api_failed",
                "error": str(error),
                "logged_at": _dt.datetime.now(tz=_dt.timezone.utc).isoformat(),
            }
        )
        log_external_generation(trace, path=self.log_path)

    # Hooks for subclasses -------------------------------------------------------
    def default_parameters(self) -> JsonDict:
        """Return default parameters merged into each request."""

        return {}

    def _build_request(self, prompt: str, parameters: JsonDict) -> JsonDict:
        """Return the outbound payload for *prompt*.

        Subclasses may override this to customise request formatting.
        """

        return {"prompt": prompt, "parameters": parameters}

    def _dispatch(self, payload: JsonDict, prompt: str, parameters: JsonDict) -> JsonDict:
        """Send *payload* to the configured transport or mock responder."""

        if self.mock_mode:
            return self._mock_response(prompt, parameters)

        if self._transport is not None:
            response = self._transport(payload)
            if not isinstance(response, dict):
                raise TypeError("transport must return a dictionary")
            return response

        if not self.endpoint:
            raise RuntimeError("live mode requested but no endpoint configured")

        return self._post_json(self.endpoint, payload, timeout=self.timeout_seconds)

    def _mock_response(self, prompt: str, parameters: JsonDict) -> JsonDict:  # pragma: no cover - abstract
        raise NotImplementedError

    def _parse_response(
        self,
        response: JsonDict,
        prompt: str,
        parameters: JsonDict,
        *,
        trace_id: str,
    ) -> JsonDict:  # pragma: no cover - abstract
        raise NotImplementedError

    # Helper methods -------------------------------------------------------------
    @staticmethod
    def _post_json(endpoint: str, payload: JsonDict, *, timeout: float) -> JsonDict:
        import urllib.error
        import urllib.request

        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            endpoint,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read().decode("utf-8")
        except urllib.error.URLError as exc:  # pragma: no cover - network path
            raise ConnectionError(f"failed to reach {endpoint}: {exc}") from exc

        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:  # pragma: no cover - network path
            raise ValueError("API returned invalid JSON") from exc

    def _normalise_asset(
        self,
        asset_payload: JsonDict,
        *,
        prompt: str,
        parameters: JsonDict,
        response: JsonDict,
        trace_id: str,
    ) -> JsonDict:
        """Return a Synesthetic asset dictionary with provenance injected."""

        asset = dict(asset_payload)
        timestamp = asset.get("timestamp") or _dt.datetime.now(tz=_dt.timezone.utc).isoformat()
        asset_id = asset.get("id") or asset.get("asset_id") or str(uuid.uuid4())
        asset["id"] = asset_id
        asset["prompt"] = prompt
        asset["timestamp"] = timestamp

        provenance = dict(asset.get("provenance") or {})
        provenance.setdefault("agent", "ExternalGenerator")
        provenance.setdefault("version", self.api_version)
        provenance["generator"] = {
            "agent": self.__class__.__name__,
            "engine": self.engine,
            "api_version": self.api_version,
            "parameters": parameters,
            "mode": "mock" if self.mock_mode else "live",
            "trace_id": trace_id,
        }
        provenance["external_response_id"] = response.get("id")
        asset["provenance"] = provenance

        canonical_sections = (
            "shader",
            "tone",
            "haptic",
            "control",
            "meta",
            "modulation",
            "rule_bundle",
        )
        for section in canonical_sections:
            asset.setdefault(section, {"component": section})

        asset.setdefault("controls", [])
        asset.setdefault("parameter_index", [])

        return asset


class GeminiGenerator(ExternalGenerator):
    engine = "gemini"
    api_version = "v1beta"

    def default_parameters(self) -> JsonDict:
        return {
            "model": os.getenv("GEMINI_MODEL", "gemini-pro"),
        }

    def _build_request(self, prompt: str, parameters: JsonDict) -> JsonDict:
        payload = super()._build_request(prompt, parameters)
        payload["safety"] = parameters.get("safety", "standard")
        return payload

    def _mock_response(self, prompt: str, parameters: JsonDict) -> JsonDict:
        timestamp = _dt.datetime.now(tz=_dt.timezone.utc).isoformat()
        return {
            "id": f"gemini-mock-{uuid.uuid4()}",
            "asset": {
                "shader": {"component": "shader", "style": "neon", "prompt": prompt},
                "tone": {"component": "tone", "mood": "serene"},
                "haptic": {"component": "haptic", "pattern": "soft"},
                "control": {"component": "control", "mappings": []},
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
        )


class OpenAIGenerator(ExternalGenerator):
    engine = "openai"
    api_version = "v1"

    def default_parameters(self) -> JsonDict:
        return {
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "temperature": float(os.getenv("OPENAI_TEMPERATURE", "0.4")),
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
                "control": {"component": "control", "mappings": []},
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
