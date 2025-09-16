"""Generator agent responsible for creating proposals for critic review."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from pathlib import Path
import uuid

from labs.logging import log_jsonl


class GeneratorAgent:
    """Produce proposal dictionaries from free-form prompts."""

    def __init__(self, log_path: str | Path | None = None) -> None:
        """Create a generator agent.

        Args:
            log_path: Optional path to the JSONL log file. When omitted the
                agent stores entries under ``meta/output/generator.jsonl``.
        """

        self._log_path = Path(log_path) if log_path is not None else Path(
            "meta/output/generator.jsonl"
        )
        self._logger = logging.getLogger(self.__class__.__name__)

    def propose(self, prompt: str) -> dict[str, object]:
        """Return a proposal dictionary for the supplied prompt."""

        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")

        proposal_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        provenance = {
            "agent": "GeneratorAgent",
            "version": "v0.1",
            "log_path": str(self._log_path),
        }
        log_record = {
            "event": "generator.propose",
            "id": proposal_id,
            "timestamp": timestamp,
            "prompt": prompt,
            "provenance": provenance,
        }
        log_jsonl(self._log_path, log_record)
        self._logger.info("Generated proposal %s", proposal_id)

        return {
            "id": proposal_id,
            "timestamp": timestamp,
            "prompt": prompt,
            "provenance": provenance,
        }


__all__ = ["GeneratorAgent"]
