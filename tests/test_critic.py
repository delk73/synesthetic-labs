"""Tests for the critic agent."""

from __future__ import annotations

from pathlib import Path

from labs.agents.critic import CriticAgent


def test_critic_detects_missing_fields(tmp_path: Path) -> None:
    critic = CriticAgent(log_path=tmp_path / "critic.jsonl")

    result = critic.review({"id": "123"})

    assert result["ok"] is False
    assert any("missing required field" in issue for issue in result["issues"])


def test_critic_accepts_valid_asset(tmp_path: Path) -> None:
    critic = CriticAgent(log_path=tmp_path / "critic.jsonl")

    asset = {
        "id": "abc",
        "timestamp": "2024-01-01T00:00:00+00:00",
        "prompt": "demo",
        "provenance": {"agent": "GeneratorAgent"},
    }

    result = critic.review(asset)

    assert result["ok"] is True
    assert result["issues"] == []
    assert result["asset"] == asset
