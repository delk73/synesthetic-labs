"""Integration test covering generator → critic handoff."""

from __future__ import annotations

from labs.agents.generator import GeneratorAgent
from labs.agents.critic import CriticAgent


def test_generator_to_critic_pipeline(tmp_path) -> None:
    generator_log = tmp_path / "generator.jsonl"
    critic_log = tmp_path / "critic.jsonl"

    generator = GeneratorAgent(log_path=str(generator_log))
    asset = generator.propose("integration prompt")

    def validator(payload: dict) -> dict:
        return {"validated": True, "asset_id": payload["id"]}

    critic = CriticAgent(validator=validator, log_path=str(critic_log))
    review = critic.review(asset)

    assert "provenance" in asset
    assert review["ok"] is True
    assert review["validation_status"] == "passed"
    assert review["mcp_response"] == {"validated": True, "asset_id": asset["id"]}
