"""Lightweight JSONL logging helper for Synesthetic Labs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


def log_jsonl(path: str | Path, record: Mapping[str, Any]) -> None:
    """Append a JSON record to a UTF-8 encoded JSONL file.

    Parameters
    ----------
    path:
        Destination file path. The parent directory is created automatically.
    record:
        Mapping to serialize as a JSON line.
    """

    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(dict(record), ensure_ascii=False, sort_keys=True)
    with path_obj.open("a", encoding="utf-8") as handle:
        handle.write(f"{line}\n")
