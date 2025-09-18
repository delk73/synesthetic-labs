"""Integration and CLI tests covering generator → critic handoff."""

from __future__ import annotations

import json
import os

from labs import cli
from labs.agents.generator import GeneratorAgent
from labs.agents.critic import CriticAgent


def test_generator_to_critic_pipeline(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("LABS_FAIL_FAST", raising=False)
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


def test_cli_critique_skips_without_fail_fast(monkeypatch, tmp_path, capsys) -> None:
    for key in ("LABS_FAIL_FAST", "MCP_HOST", "MCP_PORT", "SYN_SCHEMAS_DIR"):
        monkeypatch.delenv(key, raising=False)

    def fake_create_connection(*_args, **_kwargs):
        raise ConnectionRefusedError("connection refused")

    monkeypatch.setattr(cli.socket, "create_connection", fake_create_connection)

    generator = GeneratorAgent(log_path=str(tmp_path / "generator.jsonl"))
    asset = generator.propose("cli validation test")
    asset_path = tmp_path / "asset.json"
    asset_path.write_text(json.dumps(asset), encoding="utf-8")

    exit_code = cli.main(["critique", str(asset_path)])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["validation_status"] == "skipped"
    assert payload["ok"] is True
    assert os.environ["MCP_HOST"] == "localhost"
    assert os.environ["MCP_PORT"] == "7000"
    assert os.environ["SYN_SCHEMAS_DIR"] == os.path.join("libs", "synesthetic-schemas")


def test_cli_critique_exits_with_fail_fast(monkeypatch, tmp_path, capsys) -> None:
    for key in ("MCP_HOST", "MCP_PORT", "SYN_SCHEMAS_DIR"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("LABS_FAIL_FAST", "1")

    def fake_create_connection(*_args, **_kwargs):
        raise ConnectionRefusedError("connection refused")

    monkeypatch.setattr(cli.socket, "create_connection", fake_create_connection)

    generator = GeneratorAgent(log_path=str(tmp_path / "generator.jsonl"))
    asset = generator.propose("cli validation test")
    asset_path = tmp_path / "asset.json"
    asset_path.write_text(json.dumps(asset), encoding="utf-8")

    exit_code = cli.main(["critique", str(asset_path)])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 1
    assert payload["validation_status"] == "failed"
    assert payload["ok"] is False


def test_build_validator_uses_default_configuration(monkeypatch) -> None:
    for key in ("MCP_HOST", "MCP_PORT", "SYN_SCHEMAS_DIR", "LABS_FAIL_FAST"):
        monkeypatch.delenv(key, raising=False)

    validator = cli._build_validator()

    assert validator is not None
    instance = validator.__self__  # type: ignore[attr-defined]
    assert instance.host == "localhost"
    assert instance.port == 7000
    assert os.environ["SYN_SCHEMAS_DIR"] == os.path.join("libs", "synesthetic-schemas")
