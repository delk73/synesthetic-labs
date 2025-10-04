"""Integration and CLI tests covering generator → critic handoff."""

from __future__ import annotations

import json
import os
import types

from labs import cli
from labs.agents.generator import GeneratorAgent
from labs.agents.critic import CriticAgent
from labs.mcp_stdio import MCPUnavailableError, resolve_mcp_endpoint
from labs.generator.external import GeminiGenerator


def test_generator_to_critic_pipeline(tmp_path) -> None:
    generator_log = tmp_path / "generator.jsonl"
    critic_log = tmp_path / "critic.jsonl"

    generator = GeneratorAgent(log_path=str(generator_log))
    asset = generator.propose("integration prompt")

    def validator(payload: dict) -> dict:
        return {"validated": True, "asset_id": payload["asset_id"]}

    critic = CriticAgent(validator=validator, log_path=str(critic_log))
    review = critic.review(asset)

    assert "meta_info" in asset
    assert asset["control"]["control_parameters"]
    assert asset["modulations"]
    assert asset["rule_bundle"]["rules"]
    provenance = asset.get("provenance") or asset["meta_info"]["provenance"]["asset"]
    assert provenance["generator"]["agent"] == "GeneratorAgent"
    assert review["ok"] is True
    assert review["validation_status"] == "passed"
    assert review["mcp_response"] == {"validated": True, "asset_id": asset["asset_id"]}


def test_cli_critique_fails_when_mcp_unreachable(monkeypatch, tmp_path, capsys) -> None:

    def raise_unavailable() -> None:
        raise MCPUnavailableError("adapter missing")

    monkeypatch.setattr(cli, "build_validator_from_env", raise_unavailable)

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

    assert exit_code == 0
    review = json.loads(captured.out)
    assert review["ok"] is True
    assert review["validation_status"] == "warned"
    assert review["validation_reason"].startswith("MCP validation unavailable")


def test_cli_generate_persists_validated_asset(monkeypatch, tmp_path, capsys) -> None:
    experiments_dir = tmp_path / "experiments"
    monkeypatch.setenv("LABS_EXPERIMENTS_DIR", str(experiments_dir))

    generator_log = tmp_path / "generator.jsonl"
    critic_log = tmp_path / "critic.jsonl"

    class LoggedGeneratorAgent(GeneratorAgent):
        def __init__(self, *args, schema_version: str | None = None, **kwargs) -> None:  # pragma: no cover - construction logic trivial
            super().__init__(log_path=str(generator_log), schema_version=schema_version, *args, **kwargs)

    monkeypatch.setattr(cli, "GeneratorAgent", LoggedGeneratorAgent)

    class LoggedCriticAgent(CriticAgent):
        def __init__(self, validator=None) -> None:  # pragma: no cover - trivial init
            super().__init__(validator=validator, log_path=str(critic_log))

    monkeypatch.setattr(cli, "CriticAgent", LoggedCriticAgent)

    def validator(payload: dict) -> dict:
        return {"status": "ok", "asset_id": payload["asset_id"]}

    monkeypatch.setattr(cli, "build_validator_from_env", lambda: validator)

    exit_code = cli.main(["generate", "aurora bloom"])
    captured = capsys.readouterr()

    assert exit_code == 0

    payload = json.loads(captured.out)
    assert payload["experiment_path"]

    persisted_files = list(experiments_dir.glob("*.json"))
    assert len(persisted_files) == 1
    persisted_asset_path = persisted_files[0]

    persisted_asset = json.loads(persisted_asset_path.read_text(encoding="utf-8"))
    assert (persisted_asset.get("prompt") or persisted_asset.get("name")) == "aurora bloom"
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
    logged_prompt = logged_asset.get("prompt") or logged_asset.get("name")
    assert logged_prompt == "aurora bloom"
    provenance = logged_asset.get("provenance") or logged_asset.get("meta_info", {}).get("provenance", {}).get("asset")
    assert provenance["generator"]["agent"] == LoggedGeneratorAgent.__name__
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
        def __init__(self, *args, schema_version: str | None = None, **kwargs) -> None:  # pragma: no cover - trivial init
            super().__init__(log_path=str(generator_log), schema_version=schema_version, *args, **kwargs)

    monkeypatch.setattr(cli, "GeneratorAgent", LoggedGeneratorAgent)

    class LoggedCriticAgent(CriticAgent):
        def __init__(self, validator=None) -> None:  # pragma: no cover - trivial init
            super().__init__(validator=validator, log_path=str(critic_log))

    monkeypatch.setattr(cli, "CriticAgent", LoggedCriticAgent)

    def raise_unavailable() -> None:
        raise MCPUnavailableError("adapter missing")

    monkeypatch.setattr(cli, "build_validator_from_env", raise_unavailable)

    exit_code = cli.main(["generate", "relaxed mode prompt"])
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["review"]["validation_status"] == "warned"
    assert payload["review"]["ok"] is True
    assert payload["review"]["validation_reason"].startswith("MCP validation unavailable")

    persisted_files = list(experiments_dir.glob("*.json"))
    assert len(persisted_files) == 1


def test_cli_generate_deterministic_alias(monkeypatch, tmp_path, capsys) -> None:
    experiments_dir = tmp_path / "experiments"
    monkeypatch.setenv("LABS_EXPERIMENTS_DIR", str(experiments_dir))

    generator_log = tmp_path / "generator.jsonl"

    class LoggedGeneratorAgent(GeneratorAgent):
        def __init__(self, *args, schema_version: str | None = None, **kwargs) -> None:  # pragma: no cover - trivial init
            super().__init__(log_path=str(generator_log), schema_version=schema_version, *args, **kwargs)

    monkeypatch.setattr(cli, "GeneratorAgent", LoggedGeneratorAgent)
    monkeypatch.setattr(
        cli,
        "build_validator_from_env",
        lambda: (lambda payload: {"status": "ok", "asset_id": payload["asset_id"]}),
    )

    exit_code = cli.main(["generate", "--engine", "deterministic", "alias prompt"])
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
    gemini = GeminiGenerator(log_path=str(external_log), mock_mode=True, sleeper=lambda _: None)

    monkeypatch.setattr(cli, "build_external_generator", lambda engine: gemini)

    class LoggedCriticAgent(CriticAgent):
        def __init__(self, validator=None) -> None:  # pragma: no cover - trivial init
            super().__init__(validator=validator, log_path=str(tmp_path / "critic.jsonl"))

    monkeypatch.setattr(cli, "CriticAgent", LoggedCriticAgent)

    def validator(payload: dict) -> dict:
        return {"status": "ok", "asset_id": payload["asset_id"]}

    monkeypatch.setattr(cli, "build_validator_from_env", lambda: validator)

    exit_code = cli.main(["generate", "--engine", "gemini", "chromatic tides"])
    captured = capsys.readouterr()

    assert exit_code == 0
    output = json.loads(captured.out)
    assert output["engine"] == "gemini"
    asset = output["asset"]
    assert asset["prompt"] == "chromatic tides"
    assert asset["provenance"]["generator"]["engine"] == "gemini"

    lines = [json.loads(line) for line in external_log.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 1
    log_record = lines[0]
    assert log_record["engine"] == "gemini"
    assert log_record["status"] == "validation_passed"
    assert log_record["normalized_asset"]["meta_info"]["provenance"]["trace_id"]
    assert log_record["raw_response"]["hash"]
    assert log_record["raw_response"]["size"] > 0
    assert log_record["transport"] == output["review"]["transport"]
    assert log_record["strict"] == output["review"]["strict"]
    assert log_record["mode"] == "mock"
    assert log_record["mcp_result"] == {"status": "ok", "asset_id": asset["asset_id"]}

    persisted_files = list(experiments_dir.glob("*.json"))
    assert len(persisted_files) == 1




def test_cli_generate_flags_precedence(monkeypatch, tmp_path, capsys) -> None:
    experiments_dir = tmp_path / "experiments"
    external_log = tmp_path / "external.jsonl"
    monkeypatch.setenv("LABS_EXPERIMENTS_DIR", str(experiments_dir))
    recorded: dict[str, object] = {}

    def build_external(engine: str):
        generator = GeminiGenerator(log_path=str(external_log), mock_mode=True, sleeper=lambda _: None)
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
            recorded["parameters"] = parameters
            recorded["timeout"] = timeout
            recorded["schema_version"] = schema_version
            return original_generate(
                prompt,
                parameters=parameters,
                seed=seed,
                timeout=timeout,
                trace_id=trace_id,
                schema_version=schema_version,
            )

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
        "gemini",
        "--seed",
        "42",
        "--temperature",
        "0.85",
        "--timeout-s",
        "12",
        "--relaxed",
        "flagged prompt",
    ]
    exit_code = cli.main(args)
    captured = capsys.readouterr()

    assert exit_code == 0
    output = json.loads(captured.out)
    assert output["review"]["strict"] is False
    assert os.getenv("LABS_FAIL_FAST") == "0"
    assert recorded["seed"] == 42
    assert recorded["parameters"] == {"temperature": 0.85}
    assert recorded["timeout"] == 12.0

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
