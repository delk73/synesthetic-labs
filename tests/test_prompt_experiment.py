"""Tests for the prompt experiment harness."""

from __future__ import annotations

import json

from labs.agents.critic import CriticAgent
from labs.agents.generator import GeneratorAgent
from labs.experiments import prompt_experiment


def test_prompt_experiment_writes_asset_files(tmp_path, monkeypatch) -> None:
    prompt_file = tmp_path / "prompts.txt"
    prompt_file.write_text("shimmer\n", encoding="utf-8")
    output_dir = tmp_path / "out"

    def build_generator() -> GeneratorAgent:
        return GeneratorAgent(log_path=str(tmp_path / "generator.jsonl"))

    class LoggedCriticAgent(CriticAgent):
        def __init__(self, validator=None) -> None:  # pragma: no cover - simple wiring
            super().__init__(validator=validator, log_path=str(tmp_path / "critic.jsonl"))

    def validator(payload: dict) -> dict:
        for section in ("shader", "tone", "haptic", "control", "meta_info", "modulations", "rule_bundle"):
            assert section in payload
        return {"status": "ok", "asset_id": payload["asset_id"]}

    monkeypatch.setattr(prompt_experiment, "GeneratorAgent", build_generator)
    monkeypatch.setattr(prompt_experiment, "CriticAgent", LoggedCriticAgent)
    monkeypatch.setattr(prompt_experiment, "_ensure_validator", lambda: validator)

    exit_code = prompt_experiment.main([str(prompt_file), str(output_dir)])

    assert exit_code == 0

    run_path = output_dir / "run_1.json"
    generated_path = output_dir / "generated_assets" / "asset_1.json"
    all_results_path = output_dir / "all_results.jsonl"

    assert run_path.exists()
    assert generated_path.exists()
    assert all_results_path.exists()

    asset_data = json.loads(generated_path.read_text(encoding="utf-8"))
    assert asset_data["prompt"] == "shimmer"
    for section in ("shader", "tone", "haptic", "control", "meta_info", "modulations", "rule_bundle"):
        assert section in asset_data

    run_record = json.loads(run_path.read_text(encoding="utf-8"))
    assert run_record["review"]["validation_status"] == "passed"
    assert run_record["review"]["mcp_response"]["status"] == "ok"
