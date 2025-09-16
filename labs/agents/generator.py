"""Generator agent responsible for emitting proposal records."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Any
import uuid

from labs.logging import log_jsonl

LOGGER = logging.getLogger(__name__)


class GeneratorAgent:
    """Create structured proposals for downstream critic review."""

    def __init__(self, log_path: str | Path = "meta/output/proposals.jsonl") -> None:
        """Initialise the agent with a JSONL log destination."""

        self._log_path = Path(log_path)

    @property
    def log_path(self) -> Path:
        """Return the log path for generated proposals."""

        return self._log_path

    def propose(self, prompt: str) -> dict[str, Any]:
        """Generate a proposal for the provided prompt string."""

        record: dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prompt": prompt,
            "provenance": {
                "agent": "GeneratorAgent",
                "log_path": str(self._log_path),
            },
        }
        log_jsonl(self._log_path, record)
        LOGGER.info("Generated proposal %s", record["id"])
        return dict(record)
