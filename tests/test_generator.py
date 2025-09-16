"""Tests for the generator agent."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from labs.agents.generator import GeneratorAgent


def test_generator_produces_proposal_and_logs(tmp_path: Path) -> None:
    log_path = tmp_path / "generator.jsonl"
    agent = GeneratorAgent(log_path=log_path)

    proposal = agent.propose("demo prompt")

    assert set(proposal) == {"id", "timestamp", "prompt", "provenance"}
    assert proposal["prompt"] == "demo prompt"
    assert proposal["provenance"]["agent"] == "GeneratorAgent"

    log_lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(log_lines) == 1
    logged = json.loads(log_lines[0])
    assert logged["event"] == "generator.propose"
    assert logged["id"] == proposal["id"]


def test_generator_rejects_empty_prompts(tmp_path: Path) -> None:
    agent = GeneratorAgent(log_path=tmp_path / "log.jsonl")

    with pytest.raises(ValueError):
        agent.propose("")
