"""Generator agent responsible for proposing candidate assets."""

from __future__ import annotations

import datetime as _dt
import logging
import uuid
from typing import Any, Dict, Optional

from labs.logging import log_jsonl

_DEFAULT_LOG_PATH = "meta/output/labs/generator.jsonl"


class GeneratorAgent:
    """Generate asset proposals based on an input prompt.

    Parameters
    ----------
    log_path:
        Location of the JSONL log sink. The default targets the shared
        repository log directory under ``meta/output``.
    """

    def __init__(self, log_path: str = _DEFAULT_LOG_PATH, *, version: str = "v0.3") -> None:
        self.log_path = log_path
        self._logger = logging.getLogger(self.__class__.__name__)
        self.version = version

    def propose(self, prompt: str) -> Dict[str, Any]:
        """Return a proposal dictionary for *prompt*.

        The payload includes a UUID primary key, an ISO-8601 timestamp, the
        original prompt, and a provenance envelope. The proposal is logged to
        the configured JSONL sink for traceability.
        """

        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")

        timestamp = _dt.datetime.now(tz=_dt.timezone.utc).isoformat()
        proposal = {
            "id": str(uuid.uuid4()),
            "timestamp": timestamp,
            "prompt": prompt,
            "provenance": {
                "agent": self.__class__.__name__,
                "version": self.version,
                "logged_at": timestamp,
            },
        }

        self._logger.info("Generated proposal %s", proposal["id"])
        log_jsonl(self.log_path, proposal)
        return proposal

    def record_experiment(
        self,
        *,
        asset: Dict[str, Any],
        review: Dict[str, Any],
        experiment_path: Optional[str],
    ) -> Dict[str, Any]:
        """Log a validated experiment linking the asset to persisted output."""

        if "id" not in asset:
            raise ValueError("asset must include an 'id'")

        timestamp = _dt.datetime.now(tz=_dt.timezone.utc).isoformat()

        record = {
            "asset_id": asset["id"],
            "prompt": asset.get("prompt"),
            "experiment_path": experiment_path,
            "validation": {
                "ok": review.get("ok"),
                "issues": review.get("issues"),
                "status": review.get("validation_status"),
                "reviewed_at": review.get("reviewed_at"),
            },
            "provenance": {
                "agent": self.__class__.__name__,
                "version": self.version,
                "recorded_at": timestamp,
            },
        }

        if "timestamp" in asset:
            record["asset_timestamp"] = asset["timestamp"]

        log_jsonl(self.log_path, record)
        self._logger.info(
            "Recorded experiment for asset %s (persisted=%s)",
            asset["id"],
            bool(experiment_path),
        )
        return record
