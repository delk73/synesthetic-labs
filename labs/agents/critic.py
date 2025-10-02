"""Critic agent that reviews generator output and coordinates validation."""

from __future__ import annotations

import datetime as _dt
import logging
import os
import uuid
from typing import Any, Callable, Dict, List, Mapping, Optional

from labs.logging import log_jsonl
from labs.mcp.exceptions import MCPUnavailableError
from labs.mcp_stdio import build_validator_from_env, resolve_mcp_endpoint

_DEFAULT_LOG_PATH = "meta/output/labs/critic.jsonl"
_LABS_FAIL_FAST_ENV = "LABS_FAIL_FAST"


ValidatorType = Callable[[Dict[str, Any]], Dict[str, Any]]


def is_fail_fast_enabled() -> bool:
    """Return True unless LABS_FAIL_FAST explicitly disables strict mode."""

    raw = os.getenv(_LABS_FAIL_FAST_ENV)
    if raw is None:
        return True

    return raw.strip().lower() not in {"0", "false", "no", "off"}


class CriticAgent:
    """Review assets and surface issues before handing off to MCP validation."""

    REQUIRED_KEYS = ("asset_id", "timestamp", "prompt", "provenance")

    def __init__(
        self,
        validator: Optional[ValidatorType] = None,
        *,
        log_path: str = _DEFAULT_LOG_PATH,
    ) -> None:
        self._validator = validator
        self.log_path = log_path
        self._logger = logging.getLogger(self.__class__.__name__)

    @staticmethod
    def _resolve_trace_id(asset: Dict[str, Any]) -> str:
        meta_prov = asset.get("meta_info", {}).get("provenance", {}) if isinstance(asset, dict) else {}
        trace_id = meta_prov.get("trace_id") if isinstance(meta_prov, dict) else None
        if trace_id:
            return trace_id
        provenance = asset.get("provenance", {}) if isinstance(asset, dict) else {}
        generator_block = provenance.get("generator") if isinstance(provenance, dict) else None
        if isinstance(generator_block, dict):
            trace_id = generator_block.get("trace_id")
            if trace_id:
                return trace_id
        return str(uuid.uuid4())

    def review(self, asset: Dict[str, Any], *, patch_id: Optional[str] = None) -> Dict[str, Any]:
        """Inspect *asset* and return a review payload.

        Validation is attempted through the configured MCP validator. When
        ``LABS_FAIL_FAST`` is enabled (default) any validator outages surface as
        failures; otherwise validation still runs but surfaces as warnings so
        relaxed mode can proceed in a degraded state.
        """

        if not isinstance(asset, dict):
            raise ValueError("asset must be a dictionary")

        issues: List[str] = []
        for key in self.REQUIRED_KEYS:
            if key not in asset:
                issues.append(f"missing required field: {key}")

        fail_fast = is_fail_fast_enabled()
        validation_status = "pending"
        validation_reason: Optional[str] = None
        mcp_response: Optional[Dict[str, Any]] = None
        validation_error: Optional[Dict[str, str]] = None
        transport = resolve_mcp_endpoint()
        trace_id = self._resolve_trace_id(asset)

        def _build_error_payload(message: str, *, unavailable: bool = True) -> Dict[str, str]:
            lowered = message.lower()
            suffix: str
            if "timeout" in lowered:
                suffix = "timeout"
            elif unavailable:
                suffix = "unavailable"
            else:
                suffix = "error"
            resolved_transport = transport or "unknown"
            detail = f"{resolved_transport}_{suffix}"
            return {
                "reason": "mcp_unavailable" if unavailable else "mcp_error",
                "detail": detail,
            }
        validator = self._validator
        if validator is None:
            try:
                validator = build_validator_from_env()
                self._validator = validator
            except MCPUnavailableError as exc:
                message = f"MCP validation unavailable: {exc}"
                validation_error = _build_error_payload(str(exc))
                if fail_fast:
                    issues.append(message)
                    validation_status = "failed"
                    validation_reason = message
                    self._logger.error(message)
                else:
                    validation_status = "warned"
                    validation_reason = message
                    self._logger.warning("Validation warning: %s", message)

                    def _lazy_validator(payload: Dict[str, Any]) -> Dict[str, Any]:
                        actual_validator = build_validator_from_env()
                        return actual_validator(payload)

                    validator = _lazy_validator
                    self._validator = validator

        if validator is not None:
            try:
                response = validator(asset)
                mcp_response = response
                validation_status = "passed"
            except MCPUnavailableError as exc:
                message = f"MCP validation unavailable: {exc}"
                validation_error = _build_error_payload(str(exc))
                if fail_fast:
                    issues.append(message)
                    validation_status = "failed"
                    validation_reason = message
                    self._logger.error(message)
                else:
                    validation_status = "warned"
                    validation_reason = message
                    self._logger.warning("Validation warning: %s", message)
            except ConnectionError as exc:  # pragma: no cover - defensive fallback
                message = f"MCP validation unavailable: {exc}"
                issues.append(message)
                self._logger.error(message)
                validation_error = _build_error_payload(str(exc))
                validation_status = "failed"
                validation_reason = message
            except Exception as exc:  # pragma: no cover - unexpected failures
                message = f"MCP validation error: {exc}"
                issues.append(message)
                self._logger.error("MCP validation failed: %s", exc)
                validation_error = _build_error_payload(str(exc), unavailable=False)
                validation_status = "failed"
                validation_reason = message

        if validation_status == "pending":
            validation_status = "passed" if len(issues) == 0 else "failed"

        ok = len(issues) == 0 and validation_status in {"passed", "warned"}
        reviewed_at = _dt.datetime.now(tz=_dt.timezone.utc).isoformat()

        review = {
            "asset": asset,
            "issues": issues,
            "ok": ok,
            "reviewed_at": reviewed_at,
            "validation_status": validation_status,
            "mcp_response": mcp_response,
            "transport": transport,
            "strict": fail_fast,
            "mode": "strict" if fail_fast else "relaxed",
            "trace_id": trace_id,
        }

        if validation_reason is not None:
            review["validation_reason"] = validation_reason

        if validation_error is not None:
            review["validation_error"] = validation_error

        if patch_id is not None:
            review["patch_id"] = patch_id

        self._logger.info("Completed review for asset %s", asset.get("asset_id"))
        log_jsonl(self.log_path, review)
        return review

    def record_rating(
        self,
        *,
        patch_id: str,
        rating: Mapping[str, Any],
        asset_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Log a rating stub for *patch_id* linked to an optional *asset_id*."""

        if not patch_id:
            raise ValueError("patch_id must be a non-empty string")

        timestamp = _dt.datetime.now(tz=_dt.timezone.utc).isoformat()
        strict_flag = is_fail_fast_enabled()
        record = {
            "type": "rating",
            "patch_id": patch_id,
            "asset_id": asset_id,
            "rating": dict(rating),
            "recorded_at": timestamp,
            "trace_id": str(uuid.uuid4()),
            "strict": strict_flag,
            "mode": "strict" if strict_flag else "relaxed",
            "transport": resolve_mcp_endpoint(),
        }

        self._logger.info("Recorded rating for patch %s", patch_id)
        log_jsonl(self.log_path, record)
        return record
