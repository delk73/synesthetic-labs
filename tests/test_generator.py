"""Tests for the generator agent."""

from __future__ import annotations

import json

from labs.agents.generator import GeneratorAgent


def test_generator_propose_writes_log(tmp_path) -> None:
    log_path = tmp_path / "generator.jsonl"
    agent = GeneratorAgent(log_path=str(log_path))

    proposal = agent.propose("synthwave pulse")

    assert set(["id", "timestamp", "prompt", "provenance"]).issubset(proposal)
    assert proposal["prompt"] == "synthwave pulse"
    assert proposal["provenance"]["agent"] == "GeneratorAgent"

    assert log_path.exists()
    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    logged = json.loads(lines[0])
    assert logged["id"] == proposal["id"]
