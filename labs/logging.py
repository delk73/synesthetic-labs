"""Utilities for structured JSONL logging within Synesthetic Labs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def log_jsonl(path: str | Path, record: dict[str, Any]) -> None:
    """Append a JSON-serialisable record to a UTF-8 encoded JSONL file.

    The function ensures the parent directory exists before writing so it is
    safe to use with fresh temporary directories inside the tests.
    """

    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("a", encoding="utf-8") as handle:
        json.dump(record, handle, sort_keys=True)
        handle.write("\n")
