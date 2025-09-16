"""Critic agent that validates generator proposals."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Any

from labs.logging import log_jsonl


class CriticAgent:
    """Lightweight critic that performs structural checks on assets."""

    _REQUIRED_KEYS = ("id", "timestamp", "prompt", "provenance")

    def __init__(self, log_path: str | Path | None = None) -> None:
        """Create a critic agent.

        Args:
            log_path: Optional path to the JSONL log file. When omitted the
                agent stores entries under ``meta/output/critic.jsonl``.
        """

        self._log_path = Path(log_path) if log_path is not None else Path(
            "meta/output/critic.jsonl"
        )
        self._logger = logging.getLogger(self.__class__.__name__)

    def review(self, asset: dict[str, Any]) -> dict[str, Any]:
        """Validate a generator asset and record the results."""

        issues: list[str] = []
        for key in self._REQUIRED_KEYS:
            if key not in asset:
                issues.append(f"missing required field: {key}")

        prompt = asset.get("prompt")
        if "prompt" in asset:
            if not isinstance(prompt, str) or not prompt.strip():
                issues.append("prompt must be a non-empty string")
        if "timestamp" in asset and isinstance(asset.get("timestamp"), str):
            try:
                datetime.fromisoformat(asset["timestamp"].replace("Z", "+00:00"))
            except ValueError:
                issues.append("timestamp must be ISO-8601 formatted")

        ok = not issues
        review_record = {
            "event": "critic.review",
            "asset": asset,
            "ok": ok,
            "issues": issues,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        log_jsonl(self._log_path, review_record)
        self._logger.info("Reviewed asset %s ok=%s", asset.get("id"), ok)

        return {
            "asset": asset,
            "ok": ok,
            "issues": issues,
        }


__all__ = ["CriticAgent"]
