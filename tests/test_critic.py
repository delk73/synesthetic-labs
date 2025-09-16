from __future__ import annotations

import json
from datetime import datetime, timezone

from labs.agents.critic import CriticAgent


def test_critic_flags_missing_fields(tmp_path) -> None:
    output_path = tmp_path / "critic.log.jsonl"

    def fake_clock() -> datetime:
        return datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc)

    agent = CriticAgent(output_path=output_path, clock=fake_clock)
    proposal = {"proposal_id": "abc123"}

    review = agent.review(proposal)

    assert review["ok"] is False
    assert any("missing field" in issue for issue in review["critique"]["issues"])
    assert output_path.exists()


def test_critic_passes_valid_proposal(tmp_path) -> None:
    output_path = tmp_path / "critic.log.jsonl"

    def fake_clock() -> datetime:
        return datetime(2024, 1, 2, 11, 0, 0, tzinfo=timezone.utc)

    validation_calls: list[dict] = []

    def validator(payload):
        validation_calls.append(payload)
        return {"passed": True, "status": "ok"}

    agent = CriticAgent(output_path=output_path, clock=fake_clock, mcp_validator=validator)
    proposal = {
        "proposal_id": "p-1",
        "prompt_id": "demo",
        "prompt": {"task": "demo"},
        "asset": {"type": "demo", "description": "Shader", "constraints": {}},
        "generated_at": "2024-01-02T10:00:00+00:00",
    }

    review = agent.review(proposal)

    assert review["ok"] is True
    assert review["critique"]["issues"] == []
    assert review["validation"]["passed"] is True
    assert validation_calls and validation_calls[0] == proposal
    log_entry = json.loads(output_path.read_text(encoding="utf-8").strip().splitlines()[-1])
    assert log_entry["result"]["ok"] is True
