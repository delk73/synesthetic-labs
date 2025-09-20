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

    class LoggedCriticAgent(CriticAgent):
        def __init__(self, validator=None) -> None:  # pragma: no cover - trivial init
            super().__init__(validator=validator, log_path=str(tmp_path / "critic.jsonl"))

    monkeypatch.setattr(cli, "CriticAgent", LoggedCriticAgent)
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

    class LoggedCriticAgent(CriticAgent):
        def __init__(self, validator=None) -> None:  # pragma: no cover - trivial init
            super().__init__(validator=validator, log_path=str(tmp_path / "critic.jsonl"))

    monkeypatch.setattr(cli, "CriticAgent", LoggedCriticAgent)
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


def test_cli_generate_persists_validated_asset(monkeypatch, tmp_path, capsys) -> None:
    experiments_dir = tmp_path / "experiments"
    monkeypatch.setenv("LABS_EXPERIMENTS_DIR", str(experiments_dir))
    monkeypatch.setenv("LABS_FAIL_FAST", "1")

    generator_log = tmp_path / "generator.jsonl"
    critic_log = tmp_path / "critic.jsonl"

    class LoggedGeneratorAgent(GeneratorAgent):
        def __init__(self) -> None:  # pragma: no cover - construction logic trivial
            super().__init__(log_path=str(generator_log))

    monkeypatch.setattr(cli, "GeneratorAgent", LoggedGeneratorAgent)

    class LoggedCriticAgent(CriticAgent):
        def __init__(self, validator=None) -> None:  # pragma: no cover - trivial init
            super().__init__(validator=validator, log_path=str(critic_log))

    monkeypatch.setattr(cli, "CriticAgent", LoggedCriticAgent)

    def validator(payload: dict) -> dict:
        return {"status": "ok", "asset_id": payload["id"]}

    monkeypatch.setattr(cli, "_build_validator", lambda: validator)

    exit_code = cli.main(["generate", "aurora bloom"])
    captured = capsys.readouterr()

    assert exit_code == 0

    payload = json.loads(captured.out)
    assert payload["experiment_path"]

    persisted_files = list(experiments_dir.glob("*.json"))
    assert len(persisted_files) == 1
    persisted_asset_path = persisted_files[0]

    persisted_asset = json.loads(persisted_asset_path.read_text(encoding="utf-8"))
    assert persisted_asset["prompt"] == "aurora bloom"

    relative_path = os.path.relpath(persisted_asset_path, os.getcwd())
    assert payload["experiment_path"] == relative_path

    assert generator_log.exists()
    log_lines = generator_log.read_text(encoding="utf-8").strip().splitlines()
    assert len(log_lines) == 1
    log_record = json.loads(log_lines[0])
    assert log_record["experiment_path"] == relative_path
    assert log_record["validation"]["ok"] is True
    assert log_record["validation"]["status"] == "passed"
