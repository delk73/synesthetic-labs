"""Minimal structured logging utilities for lab agents."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping, Protocol


class LogSink(Protocol):
    """Abstract interface for structured log sinks."""

    def write(self, payload: Mapping[str, object]) -> None:  # pragma: no cover - structural protocol
        """Persist a structured payload."""


class FileLogSink:
    """Append-only JSONL log sink."""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, payload: Mapping[str, object]) -> None:
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")


class NullLogSink:
    """No-op sink used when logging is disabled."""

    def write(self, payload: Mapping[str, object]) -> None:  # pragma: no cover - trivial
        _ = payload
        return

