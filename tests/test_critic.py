from dataclasses import dataclass
from typing import Any, Mapping

import pytest

from labs.agents.critic import Critic, CriticConfig, MCPValidationResult
from labs.agents.generator import GeneratorProposal
from labs.logging import FileLogSink


@dataclass
class StubMCPAdapter:
    passed: bool

    def validate(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        return {"passed": self.passed, "details": {"echo": payload.get("parameters", {})}}


def _proposal(parameters: Mapping[str, Any]) -> GeneratorProposal:
    return GeneratorProposal(
        proposal_id="proposal-1",
        prompt_id="init",
        timestamp="2024-01-01T00:00:00+00:00",
        config_hash="abc",
        payload={
            "prompt": {"task": "demo", "objective": "ensure coverage"},
            "parameters": dict(parameters),
        },
        provenance={},
    )


def test_critic_flags_missing_parameters(tmp_path) -> None:
    critic = Critic(StubMCPAdapter(passed=True), log_sink=FileLogSink(tmp_path / "crit.jsonl"))

    result = critic.review(_proposal(parameters={}))

    assert "Proposal parameters are empty" in result.notes
    assert result.recommended_action == "revise"
    assert result.mcp == MCPValidationResult(passed=True, details={"passed": True, "details": {"echo": {}}})


def test_critic_blocks_failed_mcp(tmp_path) -> None:
    critic = Critic(StubMCPAdapter(passed=False), log_sink=FileLogSink(tmp_path / "crit.jsonl"))

    result = critic.review(_proposal(parameters={"mode": "demo"}))

    assert result.recommended_action == "block"
    assert any(note == "MCP validation failed" for note in result.notes)
    assert result.mcp.passed is False

