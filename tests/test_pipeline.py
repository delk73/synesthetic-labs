"""Integration and CLI tests covering generator → critic handoff."""

from __future__ import annotations

import json
import os
import types

from labs import cli
from labs.agents.generator import GeneratorAgent
from labs.agents.critic import CriticAgent
from labs.mcp_stdio import MCPUnavailableError, resolve_mcp_endpoint
from labs.generator.external import AzureOpenAIGenerator


def test_generator_to_critic_pipeline(tmp_path, monkeypatch) -> None:
    generator_log = tmp_path / "generator.jsonl"
    critic_log = tmp_path / "critic.jsonl"

    monkeypatch.setenv('LABS_SCHEMA_VERSION', '0.7.3')
    generator = GeneratorAgent(log_path=str(generator_log))
    asset = generator.propose("integration prompt")

    def validator(payload: dict) -> dict:
        asset_identifier = payload.get("asset_id") or payload.get("name")
        assert asset_identifier  # legacy assets omit asset_id but include name
        return {"validated": True, "asset_id": asset_identifier}

    critic = CriticAgent(validator=validator, log_path=str(critic_log))
    review = critic.review(asset)

    assert "meta_info" in asset
    assert "provenance" not in asset["meta_info"]
    assert asset["control"]["control_parameters"]
    assert asset["modulations"]
    assert asset["rule_bundle"]["rules"]
    assert review["ok"] is True
    assert review["validation_status"] == "passed"
    expected_asset_id = asset.get("asset_id") or asset["name"]
    assert review["mcp_response"]["ok"] is True
    assert review["mcp_response"]["validated"] is True
    assert review["mcp_response"]["asset_id"] == expected_asset_id


def test_cli_critique_fails_when_mcp_unreachable(monkeypatch, tmp_path, capsys) -> None:

    def raise_unavailable() -> None:
        raise MCPUnavailableError("adapter missing")

    monkeypatch.setattr(cli, "build_validator_from_env", raise_unavailable)
    monkeypatch.setenv("LABS_FAIL_FAST", "1")

    monkeypatch.setenv('LABS_SCHEMA_VERSION', '0.7.3')
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

    assert exit_code == 1
    assert captured.out == ""


def test_cli_critique_relaxed_mode_warns_validation(monkeypatch, tmp_path, capsys) -> None:

    def raise_unavailable() -> None:
        raise MCPUnavailableError("adapter missing")

    monkeypatch.setenv("LABS_FAIL_FAST", "0")
    monkeypatch.delenv("MCP_ADAPTER_CMD", raising=False)
    monkeypatch.setattr(cli, "build_validator_from_env", raise_unavailable)

    monkeypatch.setenv('LABS_SCHEMA_VERSION', '0.7.3')
    generator = GeneratorAgent(log_path=str(tmp_path / "generator.jsonl"))

    class LoggedCriticAgent(CriticAgent):
        def __init__(self, validator=None) -> None:  # pragma: no cover - trivial init
            super().__init__(validator=validator, log_path=str(tmp_path / "critic.jsonl"))

    monkeypatch.setattr(cli, "CriticAgent", LoggedCriticAgent)
    asset = generator.propose("cli validation relaxed test")
    asset_path = tmp_path / "asset.json"
    asset_path.write_text(json.dumps(asset), encoding="utf-8")

    exit_code = cli.main(["critique", str(asset_path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    review = json.loads(captured.out)
    assert review["ok"] is False
    assert review["validation_status"] in {"warned", "degraded"}
    assert review["validation_reason"].startswith("MCP validation unavailable")
    assert review["mcp_response"] == {
        "ok": False,
        "reason": "mcp_unavailable",
        "detail": "tcp_unavailable",
    }


def test_cli_generate_persists_validated_asset(monkeypatch, tmp_path, capsys) -> None:
    experiments_dir = tmp_path / "experiments"
    monkeypatch.setenv("LABS_EXPERIMENTS_DIR", str(experiments_dir))

    generator_log = tmp_path / "generator.jsonl"
    critic_log = tmp_path / "critic.jsonl"

    class LoggedGeneratorAgent(GeneratorAgent):
        def __init__(self, *, schema_version=None) -> None:  # pragma: no cover - construction logic trivial
            super().__init__(log_path=str(generator_log), schema_version=schema_version)

    monkeypatch.setattr(cli, "GeneratorAgent", LoggedGeneratorAgent)

    class LoggedCriticAgent(CriticAgent):
        def __init__(self, validator=None) -> None:  # pragma: no cover - trivial init
            super().__init__(validator=validator, log_path=str(critic_log))

    monkeypatch.setattr(cli, "CriticAgent", LoggedCriticAgent)

    def validator(payload: dict) -> dict:
        return {"status": "ok", "asset_id": payload["asset_id"]}

    monkeypatch.setattr(cli, "build_validator_from_env", lambda: validator)

    exit_code = cli.main(["generate", "--schema-version", "0.7.4", "aurora bloom"])
    captured = capsys.readouterr()

    assert exit_code == 0

    payload = json.loads(captured.out)
    assert payload["experiment_path"]

    persisted_files = list(experiments_dir.glob("*.json"))
    assert len(persisted_files) == 1
    persisted_asset_path = persisted_files[0]

    persisted_asset = json.loads(persisted_asset_path.read_text(encoding="utf-8"))
    assert persisted_asset["prompt"] == "aurora bloom"
    for section in ("shader", "tone", "haptic", "control", "meta_info", "modulations", "rule_bundle"):
        assert section in persisted_asset

    assert persisted_asset["control"]["control_parameters"]
    assert isinstance(persisted_asset["modulations"], list)

    relative_path = os.path.relpath(persisted_asset_path, os.getcwd())
    assert payload["experiment_path"] == relative_path

    assert generator_log.exists()
    log_lines = generator_log.read_text(encoding="utf-8").strip().splitlines()
    assert len(log_lines) == 2
    logged_asset = json.loads(log_lines[0])
    assert logged_asset["prompt"] == "aurora bloom"
    assert (
        logged_asset["provenance"]["generator"]["agent"]
        == LoggedGeneratorAgent.__name__
    )
    assert logged_asset["mode"] == "local"
    assert isinstance(logged_asset["strict"], bool)
    assert logged_asset["transport"] == resolve_mcp_endpoint()
    assert "trace_id" in logged_asset
    log_record = json.loads(log_lines[1])
    assert log_record["experiment_path"] == relative_path
    assert log_record["validation"]["ok"] is True
    assert log_record["validation"]["status"] == "passed"
    assert log_record["mode"] in {"strict", "relaxed"}
    assert isinstance(log_record["strict"], bool)
    assert log_record["transport"] == resolve_mcp_endpoint()


def test_cli_generate_relaxed_mode_warns_validation(monkeypatch, tmp_path, capsys) -> None:
    experiments_dir = tmp_path / "experiments"
    monkeypatch.setenv("LABS_EXPERIMENTS_DIR", str(experiments_dir))
    monkeypatch.setenv("LABS_FAIL_FAST", "0")
    monkeypatch.delenv("MCP_ADAPTER_CMD", raising=False)

    generator_log = tmp_path / "generator.jsonl"
    critic_log = tmp_path / "critic.jsonl"

    class LoggedGeneratorAgent(GeneratorAgent):
        def __init__(self, *, schema_version=None) -> None:  # pragma: no cover - trivial init
            super().__init__(log_path=str(generator_log), schema_version=schema_version)

    monkeypatch.setattr(cli, "GeneratorAgent", LoggedGeneratorAgent)

    class LoggedCriticAgent(CriticAgent):
        def __init__(self, validator=None) -> None:  # pragma: no cover - trivial init
            super().__init__(validator=validator, log_path=str(critic_log))

    monkeypatch.setattr(cli, "CriticAgent", LoggedCriticAgent)

    def raise_unavailable() -> None:
        raise MCPUnavailableError("adapter missing")

    monkeypatch.setattr(cli, "build_validator_from_env", raise_unavailable)

    exit_code = cli.main(["generate", "--schema-version", "0.7.4", "relaxed mode prompt"])
    captured = capsys.readouterr()

    assert exit_code == 1
    payload = json.loads(captured.out)
    assert payload["experiment_path"] is None
    assert payload["review"]["validation_status"] in {"warned", "degraded"}
    assert payload["review"]["ok"] is False
    assert payload["review"]["validation_reason"].startswith("MCP validation unavailable")
    assert payload["review"]["mcp_response"] == {
        "ok": False,
        "reason": "mcp_unavailable",
        "detail": "tcp_unavailable",
    }

    persisted_files = list(experiments_dir.glob("*.json"))
    assert len(persisted_files) == 0


def test_cli_generate_deterministic_alias(monkeypatch, tmp_path, capsys) -> None:
    experiments_dir = tmp_path / "experiments"
    monkeypatch.setenv("LABS_EXPERIMENTS_DIR", str(experiments_dir))

    generator_log = tmp_path / "generator.jsonl"

    class LoggedGeneratorAgent(GeneratorAgent):
        def __init__(self, *, schema_version=None) -> None:  # pragma: no cover - trivial init
            super().__init__(log_path=str(generator_log), schema_version=schema_version)

    monkeypatch.setattr(cli, "GeneratorAgent", LoggedGeneratorAgent)
    monkeypatch.setattr(
        cli,
        "build_validator_from_env",
        lambda: (lambda payload: {"status": "ok", "asset_id": payload["asset_id"]}),
    )

    exit_code = cli.main([
        "generate",
        "--engine",
        "deterministic",
        "--schema-version",
        "0.7.4",
        "alias prompt",
    ])
    captured = capsys.readouterr()

    assert exit_code == 0
    output = json.loads(captured.out)
    assert output["asset"]["prompt"] == "alias prompt"
    assert "engine" not in output
    assert output["review"]["ok"] is True

def test_cli_generate_with_external_engine(monkeypatch, tmp_path, capsys) -> None:
    experiments_dir = tmp_path / "experiments"
    monkeypatch.setenv("LABS_EXPERIMENTS_DIR", str(experiments_dir))

    external_log = tmp_path / "external.jsonl"
    azure = AzureOpenAIGenerator(log_path=str(external_log), mock_mode=True, sleeper=lambda _: None)

    monkeypatch.setattr(cli, "build_external_generator", lambda engine: azure)

    class LoggedCriticAgent(CriticAgent):
        def __init__(self, validator=None) -> None:  # pragma: no cover - trivial init
            super().__init__(validator=validator, log_path=str(tmp_path / "critic.jsonl"))

    monkeypatch.setattr(cli, "CriticAgent", LoggedCriticAgent)

    def validator(payload: dict) -> dict:
        return {"status": "ok", "asset_id": payload["asset_id"]}

    monkeypatch.setattr(cli, "build_validator_from_env", lambda: validator)

    exit_code = cli.main([
        "generate",
        "--engine",
    "azure",
        "--schema-version",
        "0.7.4",
        "chromatic tides",
    ])
    captured = capsys.readouterr()

    assert exit_code == 0
    output = json.loads(captured.out)
    assert output["engine"] == "azure"
    asset = output["asset"]
    assert asset["prompt"] == "chromatic tides"
    assert asset["provenance"]["generator"]["engine"] == "azure"

    lines = [json.loads(line) for line in external_log.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 1
    log_record = lines[0]
    assert log_record["engine"] == "azure"
    assert log_record["status"] == "validation_passed"
    assert log_record["normalized_asset"]["meta_info"]["provenance"]["trace_id"]
    assert log_record["raw_response"]["hash"]
    assert log_record["raw_response"]["size"] > 0
    assert log_record["transport"] == output["review"]["transport"]
    assert log_record["strict"] == output["review"]["strict"]
    assert log_record["mode"] == "mock"
    assert log_record["mcp_result"] == {
        "status": "ok",
        "asset_id": asset["asset_id"],
        "ok": True,
    }
    assert log_record["schema_version"] == "0.7.4"
    assert log_record["$schema"] == asset["$schema"]
    assert log_record["deployment"] == os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
    assert log_record["timestamp"] == log_record["ts"]

    persisted_files = list(experiments_dir.glob("*.json"))
    assert len(persisted_files) == 1




def test_cli_generate_flags_precedence(monkeypatch, tmp_path, capsys) -> None:
    experiments_dir = tmp_path / "experiments"
    external_log = tmp_path / "external.jsonl"
    monkeypatch.setenv("LABS_EXPERIMENTS_DIR", str(experiments_dir))
    recorded: dict[str, object] = {}

    def build_external(engine: str):
        generator = AzureOpenAIGenerator(log_path=str(external_log), mock_mode=True, sleeper=lambda _: None)
        original_generate = generator.generate

        def wrapped(
            self,
            prompt: str,
            *,
            parameters=None,
            seed=None,
            timeout=None,
            trace_id=None,
            schema_version=None,
        ):
            recorded["seed"] = seed
            recorded["timeout"] = timeout
            recorded["schema_version"] = schema_version
            asset_result = original_generate(
                prompt,
                parameters=parameters,
                seed=seed,
                timeout=timeout,
                trace_id=trace_id,
                schema_version=schema_version,
            )
            if isinstance(asset_result, tuple) and len(asset_result) == 2:
                asset_payload, context = asset_result
                context_parameters = context.get("parameters") if isinstance(context, dict) else None
                if isinstance(context_parameters, dict):
                    recorded["parameters"] = context_parameters
                elif isinstance(parameters, dict):
                    recorded["parameters"] = parameters
                else:
                    recorded["parameters"] = {}
                return asset_payload, context
            if isinstance(parameters, dict):
                recorded["parameters"] = parameters
            else:
                recorded["parameters"] = {}
            return asset_result

        generator.generate = types.MethodType(wrapped, generator)
        return generator

    monkeypatch.setattr(cli, "build_external_generator", build_external)

    class LoggedCriticAgent(CriticAgent):
        def __init__(self, validator=None) -> None:  # pragma: no cover - trivial init
            super().__init__(validator=validator, log_path=str(tmp_path / "critic.jsonl"))

    monkeypatch.setattr(cli, "CriticAgent", LoggedCriticAgent)
    monkeypatch.setattr(cli, "build_validator_from_env", lambda: (lambda payload: {"status": "ok", "asset_id": payload["asset_id"]}))

    args = [
        "generate",
        "--engine",
    "azure",
        "--seed",
        "42",
        "--temperature",
        "0.85",
        "--timeout-s",
        "12",
        "--relaxed",
        "--schema-version",
        "0.7.4",
        "flagged prompt",
    ]
    exit_code = cli.main(args)
    captured = capsys.readouterr()

    assert exit_code == 0
    output = json.loads(captured.out)
    assert output["review"]["strict"] is False
    assert os.getenv("LABS_FAIL_FAST") == "0"
    assert recorded["seed"] == 42
    assert recorded["parameters"]["temperature"] == 0.85
    assert recorded["parameters"]["schema_version"] == "0.7.4"
    assert recorded["timeout"] == 12.0
    assert recorded["schema_version"] == "0.7.4"

def test_cli_preview_command(monkeypatch, capsys) -> None:
    asset = {"asset_id": "asset-10"}
    patch = {"id": "patch-10"}

    def fake_preview(payload_asset, payload_patch):
        assert payload_asset == asset
        assert payload_patch == patch
        return {"action": "preview", "asset_id": asset["asset_id"], "patch_id": patch["id"]}

    monkeypatch.setattr(cli, "preview_patch", fake_preview)

    exit_code = cli.main(["preview", json.dumps(asset), json.dumps(patch)])
    captured = capsys.readouterr()

    assert exit_code == 0
    output = json.loads(captured.out)
    assert output["patch_id"] == patch["id"]


def test_cli_apply_command(monkeypatch, capsys) -> None:
    asset = {"asset_id": "asset-20"}
    patch = {"id": "patch-20"}

    def fake_build_validator_optional():
        return lambda payload: {"status": "ok", "asset_id": payload["asset_id"]}

    def fake_apply(payload_asset, payload_patch, critic):
        assert payload_asset == asset
        assert payload_patch == patch
        assert critic is not None
        return {"asset": payload_asset, "review": {"ok": True}}

    monkeypatch.setattr(cli, "_build_validator_optional", fake_build_validator_optional)
    monkeypatch.setattr(cli, "apply_patch", fake_apply)

    exit_code = cli.main(["apply", json.dumps(asset), json.dumps(patch)])
    captured = capsys.readouterr()

    assert exit_code == 0
    output = json.loads(captured.out)
    assert output["review"]["ok"] is True


def test_cli_rate_command(monkeypatch, capsys) -> None:
    rating = {"score": 0.9}

    recorded = {}

    def fake_rate(patch_id, payload_rating, asset_id=None):
        recorded["patch_id"] = patch_id
        recorded["rating"] = payload_rating
        recorded["asset_id"] = asset_id
        return {"action": "rate", "patch_id": patch_id, "rating": payload_rating, "asset_id": asset_id}

    monkeypatch.setattr(cli, "rate_patch", fake_rate)

    exit_code = cli.main(["rate", "patch-30", json.dumps(rating), "--asset-id", "asset-30"])
    captured = capsys.readouterr()

    assert exit_code == 0
    output = json.loads(captured.out)
    assert output["rating"] == rating
    assert recorded["asset_id"] == "asset-30"
