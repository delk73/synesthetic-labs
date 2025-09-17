"""Utilities for structured logging in Synesthetic Labs."""

from __future__ import annotations

import json
import os
from typing import Any, Dict


def log_jsonl(path: str, record: Dict[str, Any]) -> None:
    """Append *record* as a JSON line to *path*.

    The function ensures the target directory exists and writes UTF-8 encoded
    JSON with a trailing newline so that downstream tooling can consume the log
    as a JSONL stream.
    """

    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True))
        handle.write("\n")
