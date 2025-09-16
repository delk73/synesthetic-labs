"""Critic agent responsible for validating proposal structure."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Any

from labs.logging import log_jsonl

LOGGER = logging.getLogger(__name__)


class CriticAgent:
    """Review generator proposals and surface structural issues."""

    def __init__(self, log_path: str | Path = "meta/output/reviews.jsonl") -> None:
        """Initialise the critic with a JSONL log destination."""

        self._log_path = Path(log_path)

    @property
    def log_path(self) -> Path:
        """Return the log path for recorded reviews."""

        return self._log_path

    def review(self, asset: dict[str, Any]) -> dict[str, Any]:
        """Validate the provided asset and return the augmented record."""

        issues: list[str] = []
        required_keys = ("id", "timestamp", "prompt", "provenance")
        for key in required_keys:
            if key not in asset:
                issues.append(f"Missing key: {key}")
        if "provenance" in asset and not isinstance(asset.get("provenance"), dict):
            issues.append("Provenance must be a mapping")

        ok = not issues
        review_record = {
            "asset": dict(asset),
            "asset_id": asset.get("id"),
            "issues": list(issues),
            "ok": ok,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        log_jsonl(self._log_path, review_record)
        LOGGER.info("Reviewed asset %s ok=%s", asset.get("id"), ok)

        result = dict(asset)
        result["ok"] = ok
        result["issues"] = list(issues)
        return result
