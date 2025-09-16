"""Tests for the generator agent."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import uuid

from labs.agents.generator import GeneratorAgent


def test_generator_produces_record_and_logs(tmp_path: Path) -> None:
    """Generator should emit a proposal and write it to the log."""

    log_path = tmp_path / "generator.jsonl"
    agent = GeneratorAgent(log_path=log_path)
    proposal = agent.propose("demo prompt")

    assert proposal["prompt"] == "demo prompt"
    uuid.UUID(proposal["id"])  # Raises ValueError if invalid
    datetime.fromisoformat(proposal["timestamp"])  # Should parse without error
    assert proposal["provenance"]["log_path"] == str(log_path)

    log_lines = [line for line in log_path.read_text(encoding="utf-8").splitlines() if line]
    assert len(log_lines) == 1
    logged_record = json.loads(log_lines[0])
    assert logged_record == proposal
