"""End-to-end test for generator and critic cooperation."""

from __future__ import annotations

import json
from pathlib import Path

from labs.agents.critic import CriticAgent
from labs.agents.generator import GeneratorAgent


def test_pipeline_round_trip(tmp_path: Path) -> None:
    log_path = tmp_path / "pipeline.jsonl"
    generator = GeneratorAgent(log_path=log_path)
    critic = CriticAgent(log_path=log_path)

    proposal = generator.propose("pipeline prompt")
    review = critic.review(proposal)

    assert proposal["provenance"]["agent"] == "GeneratorAgent"
    assert review["ok"] is True
    assert review["asset"]["id"] == proposal["id"]

    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    second = json.loads(lines[1])
    assert first["event"] == "generator.propose"
    assert second["event"] == "critic.review"
    assert second["asset"]["id"] == proposal["id"]
