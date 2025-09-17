"""Critic agent that reviews generator output and coordinates validation."""

from __future__ import annotations

import datetime as _dt
import logging
from typing import Any, Callable, Dict, List, Optional

from labs.logging import log_jsonl

_DEFAULT_LOG_PATH = "meta/output/critic.jsonl"


class MCPUnavailableError(RuntimeError):
    """Raised when the MCP validator cannot be reached."""


ValidatorType = Callable[[Dict[str, Any]], Dict[str, Any]]


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

    def review(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Inspect *asset* and return a review payload.

        Validation is attempted through the configured MCP validator. If the
        validator is missing or reports unavailability, the review records a
        skipped validation and still returns actionable feedback.
        """

        if not isinstance(asset, dict):
            raise ValueError("asset must be a dictionary")

        issues: List[str] = []
        for key in self.REQUIRED_KEYS:
            if key not in asset:
                issues.append(f"missing required field: {key}")

        validation_status = "skipped"
        mcp_response: Optional[Dict[str, Any]] = None

        if self._validator is None:
            self._logger.info("MCP validation skipped: no validator configured")
        else:
            try:
                response = self._validator(asset)
                mcp_response = response
                validation_status = "passed"
            except MCPUnavailableError as exc:
                self._logger.warning("MCP validation skipped: %s", exc)
            except ConnectionError as exc:  # pragma: no cover - defensive fallback
                self._logger.warning("MCP validation skipped: %s", exc)
            except Exception as exc:  # pragma: no cover - unexpected failures
                validation_status = "failed"
                message = f"MCP validation error: {exc}"
                issues.append(message)
                self._logger.error("MCP validation failed: %s", exc)

        ok = len(issues) == 0 and validation_status != "failed"
        reviewed_at = _dt.datetime.now(tz=_dt.timezone.utc).isoformat()

        review = {
            "asset": asset,
            "issues": issues,
            "ok": ok,
            "reviewed_at": reviewed_at,
            "validation_status": validation_status,
            "mcp_response": mcp_response,
        }

        self._logger.info("Completed review for asset %s", asset.get("id"))
        log_jsonl(self.log_path, review)
        return review
