"""Tests for the critic agent."""

from __future__ import annotations

import logging
import sys

import pytest

from labs import mcp_stdio
from labs.agents.critic import CriticAgent, MCPUnavailableError


@pytest.fixture()
def base_asset() -> dict:
    return {
        "id": "proposal-1",
        "timestamp": "2024-01-01T00:00:00+00:00",
        "prompt": "aurora sweep",
        "provenance": {"agent": "GeneratorAgent"},
    }


def test_missing_fields_flagged(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("MCP_ENDPOINT", "tcp")
    monkeypatch.delenv("LABS_FAIL_FAST", raising=False)
    critic = CriticAgent(log_path=str(tmp_path / "critic.jsonl"))
    review = critic.review({"id": "only"})

    assert review["ok"] is False
    assert any("missing required field" in item for item in review["issues"])
    assert any("MCP validation unavailable" in item for item in review["issues"])
    assert review["validation_status"] == "failed"
    assert review["mcp_response"] is None
    assert review["validation_error"] == {
        "reason": "mcp_unavailable",
        "detail": "tcp_unavailable",
    }


def test_successful_validation(tmp_path, base_asset) -> None:

    def validator(payload: dict) -> dict:
        return {"status": "ok", "asset_id": payload["id"]}

    critic = CriticAgent(validator=validator, log_path=str(tmp_path / "critic.jsonl"))
    review = critic.review(base_asset)

    assert review["ok"] is True
    assert review["issues"] == []
    assert review["validation_status"] == "passed"
    assert review["mcp_response"] == {"status": "ok", "asset_id": "proposal-1"}
    assert "validation_reason" not in review


def test_validation_failure_when_mcp_unavailable(tmp_path, base_asset, caplog, monkeypatch) -> None:
    monkeypatch.setenv("MCP_ENDPOINT", "tcp")

    def validator(_: dict) -> dict:
        raise MCPUnavailableError("adapter offline")

    critic = CriticAgent(validator=validator, log_path=str(tmp_path / "critic.jsonl"))

    with caplog.at_level(logging.ERROR):
        review = critic.review(base_asset)

    assert review["ok"] is False
    assert review["validation_status"] == "failed"
    assert any("adapter offline" in issue for issue in review["issues"])
    assert any("MCP validation unavailable" in message for message in caplog.messages)
    assert review["validation_reason"].startswith("MCP validation unavailable")
    assert review["validation_error"] == {
        "reason": "mcp_unavailable",
        "detail": "tcp_unavailable",
    }


def test_validation_failure_records_issue(tmp_path, base_asset, monkeypatch) -> None:
    monkeypatch.setenv("MCP_ENDPOINT", "tcp")

    def validator(_: dict) -> dict:
        raise RuntimeError("schema mismatch")

    critic = CriticAgent(validator=validator, log_path=str(tmp_path / "critic.jsonl"))
    review = critic.review(base_asset)

    assert review["ok"] is False
    assert any("MCP validation error" in issue for issue in review["issues"])
    assert review["validation_status"] == "failed"
    assert review["validation_reason"] == "MCP validation error: schema mismatch"
    assert review["validation_error"] == {
        "reason": "mcp_error",
        "detail": "tcp_error",
    }


def test_critic_fails_when_stdio_validator_unavailable(tmp_path, base_asset, monkeypatch, caplog) -> None:
    monkeypatch.setenv("MCP_ENDPOINT", "stdio")

    def raise_unavailable(*_args, **_kwargs):
        raise MCPUnavailableError("adapter not configured")

    monkeypatch.setattr("labs.agents.critic.build_validator_from_env", raise_unavailable)

    critic = CriticAgent(log_path=str(tmp_path / "critic.jsonl"))

    with caplog.at_level(logging.ERROR):
        review = critic.review(base_asset)

    assert review["ok"] is False
    assert review["validation_status"] == "failed"
    assert any("adapter not configured" in issue for issue in review["issues"])
    assert any("adapter not configured" in message for message in caplog.messages)
    assert review["validation_reason"].startswith("MCP validation unavailable")
    assert review["validation_error"] == {
        "reason": "mcp_unavailable",
        "detail": "stdio_unavailable",
    }


def test_critic_reports_missing_mcp_command(tmp_path, base_asset, monkeypatch, caplog) -> None:
    monkeypatch.setenv("MCP_ENDPOINT", "stdio")
    monkeypatch.delenv("MCP_ADAPTER_CMD", raising=False)

    critic = CriticAgent(log_path=str(tmp_path / "critic.jsonl"))

    with caplog.at_level(logging.ERROR):
        review = critic.review(base_asset)

    assert review["ok"] is False
    assert any("MCP validation unavailable" in issue for issue in review["issues"])
    assert any("MCP validation unavailable" in message for message in caplog.messages)
    assert review["validation_reason"].startswith("MCP validation unavailable")
    assert review["validation_error"] == {
        "reason": "mcp_unavailable",
        "detail": "stdio_unavailable",
    }


def test_critic_handles_stub_failure(tmp_path, base_asset, monkeypatch, caplog) -> None:
    monkeypatch.setenv("MCP_ENDPOINT", "stdio")
    command = f"{sys.executable} -m labs.mcp_stub --fail"
    monkeypatch.setenv("MCP_ADAPTER_CMD", command)

    critic = CriticAgent(log_path=str(tmp_path / "critic.jsonl"))

    with caplog.at_level(logging.ERROR):
        review = critic.review(base_asset)

    assert review["ok"] is False
    assert review["validation_status"] == "failed"
    assert any("MCP validation unavailable" in issue for issue in review["issues"])
    assert any("MCP validation unavailable" in message for message in caplog.messages)
    assert review["validation_reason"].startswith("MCP validation unavailable")
    assert review["validation_error"] == {
        "reason": "mcp_unavailable",
        "detail": "stdio_unavailable",
    }


def test_relaxed_mode_warns_when_validator_unavailable(tmp_path, base_asset, monkeypatch, caplog) -> None:
    monkeypatch.setenv("LABS_FAIL_FAST", "0")
    monkeypatch.setenv("MCP_ENDPOINT", "tcp")

    def raise_unavailable(*_args, **_kwargs):
        raise MCPUnavailableError("adapter offline")

    monkeypatch.setattr("labs.agents.critic.build_validator_from_env", raise_unavailable)

    critic = CriticAgent(log_path=str(tmp_path / "critic.jsonl"))

    with caplog.at_level(logging.WARNING):
        review = critic.review(base_asset)

    assert review["ok"] is True
    assert review["issues"] == []
    assert review["validation_status"] == "warned"
    assert review["mcp_response"] is None
    assert review["validation_reason"].startswith("MCP validation unavailable")
    assert any("Validation warning" in message for message in caplog.messages)
    assert review["validation_error"] == {
        "reason": "mcp_unavailable",
        "detail": "tcp_unavailable",
    }


def test_socket_endpoint_without_path_emits_socket_detail(tmp_path, base_asset, monkeypatch) -> None:
    monkeypatch.setenv("MCP_ENDPOINT", "socket")
    monkeypatch.delenv("MCP_SOCKET_PATH", raising=False)

    critic = CriticAgent(log_path=str(tmp_path / "critic.jsonl"))
    review = critic.review(base_asset)

    assert review["ok"] is False
    assert any("MCP validation unavailable" in issue for issue in review["issues"])
    assert review["validation_status"] == "failed"
    assert review["validation_error"] == {
        "reason": "mcp_unavailable",
        "detail": "socket_unavailable",
    }


def test_schemas_dir_emits_single_warning(monkeypatch, caplog, tmp_path) -> None:
    monkeypatch.setenv("MCP_ENDPOINT", "stdio")
    monkeypatch.setenv("MCP_ADAPTER_CMD", f"{sys.executable} -m labs.mcp_stub")
    monkeypatch.setenv("SYN_SCHEMAS_DIR", str(tmp_path / "schemas"))
    mcp_stdio._SCHEMAS_WARNING_EMITTED = False

    with caplog.at_level(logging.WARNING):
        validator = mcp_stdio.build_validator_from_env()
        assert callable(validator)
        another_validator = mcp_stdio.build_validator_from_env()
        assert callable(another_validator)

    warnings = [record for record in caplog.records if "SYN_SCHEMAS_DIR is deprecated" in record.message]
    assert len(warnings) == 1
    assert "STDIO" in warnings[0].message
