"""Critic agent that reviews generator output and coordinates validation."""

from __future__ import annotations

import datetime as _dt
import logging
import os
from typing import Any, Callable, Dict, List, Mapping, Optional

from labs.logging import log_jsonl
from labs.mcp.exceptions import MCPUnavailableError
from labs.mcp_stdio import build_validator_from_env

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

    REQUIRED_KEYS = ("id", "timestamp", "prompt", "provenance")

    def __init__(
        self,
        validator: Optional[ValidatorType] = None,
        *,
        log_path: str = _DEFAULT_LOG_PATH,
    ) -> None:
        self._validator = validator
        self.log_path = log_path
        self._logger = logging.getLogger(self.__class__.__name__)

    def review(self, asset: Dict[str, Any], *, patch_id: Optional[str] = None) -> Dict[str, Any]:
        """Inspect *asset* and return a review payload.

        Validation is attempted through the configured MCP validator. When
        ``LABS_FAIL_FAST`` is enabled (default) any validator outages surface as
        failures; otherwise validation is skipped and the review may proceed in
        a relaxed mode.
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
        endpoint = os.getenv("MCP_ENDPOINT", "stdio").strip().lower() or "stdio"

        def _build_error_payload(message: str, *, unavailable: bool = True) -> Dict[str, str]:
            detail = "unknown"
            lowered = message.lower()
            if endpoint == "tcp":
                if "timeout" in lowered:
                    detail = "tcp_timeout"
                else:
                    detail = "tcp_connect_failed"
            elif endpoint == "socket":
                detail = "socket_unavailable"
            else:
                detail = "stdio_unavailable"
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
                    validation_status = "skipped"
                    validation_reason = message
                    self._logger.warning("Validation skipped: %s", message)

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
                    validation_status = "skipped"
                    validation_reason = message
                    self._logger.warning("Validation skipped: %s", message)
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

        ok = len(issues) == 0 and validation_status in {"passed", "skipped"}
        reviewed_at = _dt.datetime.now(tz=_dt.timezone.utc).isoformat()

        review = {
            "asset": asset,
            "issues": issues,
            "ok": ok,
            "reviewed_at": reviewed_at,
            "validation_status": validation_status,
            "mcp_response": mcp_response,
        }

        if validation_reason is not None:
            review["validation_reason"] = validation_reason

        if validation_error is not None:
            review["validation_error"] = validation_error

        if patch_id is not None:
            review["patch_id"] = patch_id

        self._logger.info("Completed review for asset %s", asset.get("id"))
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
        record = {
            "type": "rating",
            "patch_id": patch_id,
            "asset_id": asset_id,
            "rating": dict(rating),
            "recorded_at": timestamp,
        }

        self._logger.info("Recorded rating for patch %s", patch_id)
        log_jsonl(self.log_path, record)
        return record
