"""Tests for the critic agent."""

from __future__ import annotations

import logging

import pytest

from labs.agents.critic import CriticAgent, MCPUnavailableError


@pytest.fixture()
def base_asset() -> dict:
    return {
        "id": "proposal-1",
        "timestamp": "2024-01-01T00:00:00+00:00",
        "prompt": "aurora sweep",
        "provenance": {"agent": "GeneratorAgent"},
    }


def test_missing_fields_flagged(tmp_path) -> None:
    critic = CriticAgent(log_path=str(tmp_path / "critic.jsonl"))
    review = critic.review({"id": "only"})

    assert review["ok"] is False
    assert any("missing required field" in item for item in review["issues"])
    assert review["validation_status"] == "skipped"
    assert review["mcp_response"] is None


def test_successful_validation(tmp_path, base_asset) -> None:
    def validator(payload: dict) -> dict:
        return {"status": "ok", "asset_id": payload["id"]}

    critic = CriticAgent(validator=validator, log_path=str(tmp_path / "critic.jsonl"))
    review = critic.review(base_asset)

    assert review["ok"] is True
    assert review["issues"] == []
    assert review["validation_status"] == "passed"
    assert review["mcp_response"] == {"status": "ok", "asset_id": "proposal-1"}


def test_validation_skipped_logs_message(tmp_path, base_asset, caplog) -> None:
    def validator(_: dict) -> dict:
        raise MCPUnavailableError("adapter offline")

    critic = CriticAgent(validator=validator, log_path=str(tmp_path / "critic.jsonl"))

    with caplog.at_level(logging.WARNING):
        review = critic.review(base_asset)

    assert review["validation_status"] == "skipped"
    assert any("validation skipped" in message for message in caplog.messages)


def test_validation_failure_records_issue(tmp_path, base_asset) -> None:
    def validator(_: dict) -> dict:
        raise RuntimeError("schema mismatch")

    critic = CriticAgent(validator=validator, log_path=str(tmp_path / "critic.jsonl"))
    review = critic.review(base_asset)

    assert review["ok"] is False
    assert any("MCP validation error" in issue for issue in review["issues"])
    assert review["validation_status"] == "failed"
