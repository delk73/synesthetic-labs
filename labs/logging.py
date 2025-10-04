"""Utilities for structured logging in Synesthetic Labs."""

from __future__ import annotations

import datetime as _dt
import json
import os
from typing import Any, Dict, Optional

_EXTERNAL_LOG_PATH = "meta/output/labs/external.jsonl"


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


def log_external_generation(record: Dict[str, Any], *, path: Optional[str] = None) -> None:
    """Append *record* to the external generator log stream."""

    payload = dict(record)
    payload.setdefault("timestamp", _dt.datetime.now(tz=_dt.timezone.utc).isoformat())
    log_jsonl(path or _EXTERNAL_LOG_PATH, payload)
