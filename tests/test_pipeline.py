"""Integration tests covering the generator → critic pipeline."""

from __future__ import annotations

import json
from pathlib import Path

from labs.agents.critic import CriticAgent
from labs.agents.generator import GeneratorAgent


def test_generator_to_critic_pipeline(tmp_path: Path) -> None:
    """Running the pipeline should produce consistent proposal and review logs."""

    generator_log = tmp_path / "generator.jsonl"
    critic_log = tmp_path / "critic.jsonl"

    generator = GeneratorAgent(log_path=generator_log)
    proposal = generator.propose("pipeline prompt")

    critic = CriticAgent(log_path=critic_log)
    review = critic.review(proposal)

    assert "provenance" in proposal
    assert review["ok"] is True
    assert review["issues"] == []
    assert review["prompt"] == proposal["prompt"]

    generator_lines = [line for line in generator_log.read_text(encoding="utf-8").splitlines() if line]
    critic_lines = [line for line in critic_log.read_text(encoding="utf-8").splitlines() if line]
    assert json.loads(generator_lines[0])["id"] == proposal["id"]
    assert json.loads(critic_lines[0])["asset_id"] == proposal["id"]
    assert json.loads(critic_lines[0])["ok"] is True
