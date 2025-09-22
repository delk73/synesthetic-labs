"""Generator agent responsible for proposing candidate assets."""

from __future__ import annotations

import datetime as _dt
import logging
from typing import Any, Dict, Optional

from labs.logging import log_jsonl
from labs.generator.assembler import AssetAssembler

_DEFAULT_LOG_PATH = "meta/output/labs/generator.jsonl"


class GeneratorAgent:
    """Generate asset proposals based on an input prompt.

    Parameters
    ----------
    log_path:
        Location of the JSONL log sink. The default targets the shared
        repository log directory under ``meta/output``.
    """

    def __init__(
        self,
        log_path: str = _DEFAULT_LOG_PATH,
        *,
        version: str = "v0.1",
        assembler: Optional[AssetAssembler] = None,
    ) -> None:
        self.log_path = log_path
        self._logger = logging.getLogger(self.__class__.__name__)
        self.version = version
        self._assembler = assembler or AssetAssembler(version=version)

    def propose(self, prompt: str, *, seed: Optional[int] = None) -> Dict[str, Any]:
        """Return a fully assembled asset for *prompt*.

        The payload mirrors the canonical Synesthetic schema sections produced
        by :class:`AssetAssembler` and is logged to the configured JSONL sink
        for traceability.
        """

        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")

        asset = self._assembler.generate(prompt, seed=seed)

        timestamp = asset.get("timestamp") or _dt.datetime.now(tz=_dt.timezone.utc).isoformat()
        provenance = asset.setdefault("provenance", {})
        provenance.setdefault("agent", "AssetAssembler")
        provenance.setdefault("version", self._assembler.version)
        provenance["generator"] = {
            "agent": self.__class__.__name__,
            "version": self.version,
            "generated_at": timestamp,
        }

        self._logger.info("Generated asset %s", asset.get("id"))
        log_jsonl(self.log_path, asset)
        return asset

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
