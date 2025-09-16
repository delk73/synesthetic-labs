"""Utility helpers for structured logging in Synesthetic Labs."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def log_jsonl(path: Path | str, record: Dict[str, Any]) -> Path:
    """Append *record* as a JSON line to *path* and return the resolved path."""
    log_path = Path(path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        json.dump(record, handle, sort_keys=True)
        handle.write("\n")
    return log_path
