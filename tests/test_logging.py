"""Logging helper tests."""

from __future__ import annotations

import json

from labs.logging import log_external_generation


def test_log_external_generation_writes_timestamp(tmp_path) -> None:
    path = tmp_path / "external.jsonl"
    record = {"engine": "gemini", "status": "validation_passed"}

    log_external_generation(record, path=str(path))

    lines = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 1
    assert lines[0]["engine"] == "gemini"
    assert lines[0]["status"] == "validation_passed"
    assert "timestamp" in lines[0]
