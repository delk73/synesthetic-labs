"""Generator agent responsible for proposing candidate assets."""

from __future__ import annotations

import datetime as _dt
import logging
import uuid
from typing import Any, Dict

from labs.logging import log_jsonl

_DEFAULT_LOG_PATH = "meta/output/generator.jsonl"


class GeneratorAgent:
    """Generate asset proposals based on an input prompt.

    Parameters
    ----------
    log_path:
        Location of the JSONL log sink. The default targets the shared
        repository log directory under ``meta/output``.
    """

    def __init__(self, log_path: str = _DEFAULT_LOG_PATH) -> None:
        self.log_path = log_path
        self._logger = logging.getLogger(self.__class__.__name__)

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
                "version": "v0.1",
                "logged_at": timestamp,
            },
        }

        self._logger.info("Generated proposal %s", proposal["id"])
        log_jsonl(self.log_path, proposal)
        return proposal
