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

        schema_version = 'unknown'
        schema_url = asset.get('$schema')
        if isinstance(schema_url, str) and '/' in schema_url:
            try:
                schema_version = schema_url.split('/')[-2]
            except Exception:
                pass
        requires_enriched = schema_version >= '0.7.4'

        base_required = []
        enriched_required = ['asset_id', 'timestamp', 'prompt', 'provenance']

        required_fields = enriched_required if requires_enriched else base_required
        for field in required_fields:
            if field not in asset:
                issues.append(f'missing required field: {field}')

        fail_fast = is_fail_fast_enabled()
        validation_status = "pending"
        validation_reason: Optional[str] = None
        mcp_response: Optional[Dict[str, Any]] = None
        validation_error: Optional[Dict[str, str]] = None
        transport = resolve_mcp_endpoint()
        trace_id = self._resolve_trace_id(asset)
        should_attempt_validation = True

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

        if issues:
            # Only treat as fatal for enriched schemas
            if requires_enriched:
                message = "MCP validation unavailable: asset missing required fields"
                issues.append(message)
                validation_error = _build_error_payload(message)
                validation_reason = message
                if fail_fast:
                    validation_status = "failed"
                    should_attempt_validation = False
                    self._logger.error(message)
                else:
                    validation_status = "warned"
                    self._logger.warning("Validation warning: %s", message)

        validator = None
        if should_attempt_validation:
            validator = self._validator
            if validator is None:
                try:
                    validator = build_validator_from_env()
                    self._validator = validator
                except MCPUnavailableError as exc:
                    message = f"MCP validation unavailable: {exc}"
                    if fail_fast:
                        validation_error = _build_error_payload(str(exc))
                        mcp_response = {"ok": False, **validation_error}
                        issues.append(message)
                        validation_status = "failed"
                        validation_reason = message
                        self._logger.error(message)
                        should_attempt_validation = False
                    else:
                        validation_status = "degraded"
                        validation_reason = message
                        validation_error = _build_error_payload(str(exc))
                        mcp_response = {"ok": False, **validation_error}
                        self._logger.warning("Validation warning (degraded): %s", message)
                        validator = None
                        should_attempt_validation = False

        if should_attempt_validation and validator is not None:
            try:
                response = validator(asset)
                if isinstance(response, dict):
                    mcp_response = dict(response)
                    mcp_response.setdefault("ok", True)
                else:
                    mcp_response = {"ok": True}
                if validation_status == "pending":
                    validation_status = "passed"
            except MCPUnavailableError as exc:
                message = f"MCP validation unavailable: {exc}"
                if fail_fast:
                    validation_error = _build_error_payload(str(exc))
                    mcp_response = {"ok": False, **validation_error}
                    issues.append(message)
                    validation_status = "failed"
                    validation_reason = message
                    self._logger.error(message)
                else:
                    validation_status = "degraded"
                    validation_reason = message
                    validation_error = _build_error_payload(str(exc))
                    mcp_response = {"ok": False, **validation_error}
                    self._logger.warning("Validation warning (degraded): %s", message)
            except ConnectionError as exc:  # pragma: no cover - defensive fallback
                message = f"MCP validation unavailable: {exc}"
                issues.append(message)
                self._logger.error(message)
                validation_error = _build_error_payload(str(exc))
                mcp_response = {"ok": False, **validation_error}
                validation_status = "failed"
                validation_reason = message
            except Exception as exc:  # pragma: no cover - unexpected failures
                message = f"MCP validation error: {exc}"
                issues.append(message)
                self._logger.error("MCP validation failed: %s", exc)
                validation_error = _build_error_payload(str(exc), unavailable=False)
                mcp_response = {"ok": False, **validation_error}
                validation_status = "failed"
                validation_reason = message

        if validation_status == "pending":
            validation_status = "passed" if len(issues) == 0 else "failed"

        if mcp_response is None:
            if validation_error is not None:
                mcp_response = {"ok": False, **validation_error}
            elif validation_status in {"passed", "warned"} and len(issues) == 0:
                mcp_response = {"ok": True}
            else:
                mcp_response = {"ok": False, "reason": "validation_not_attempted"}

        mcp_ok = bool(mcp_response.get("ok"))
        ok = mcp_ok and (len(issues) == 0 and validation_status in {"passed", "warned"})
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
