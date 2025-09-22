"""Tests for the prompt experiment harness."""

from __future__ import annotations

import json

from labs.experiments import prompt_experiment


def test_prompt_experiment_writes_asset_files(tmp_path, monkeypatch) -> None:
    prompt_file = tmp_path / "prompts.txt"
    prompt_file.write_text("shimmer\n", encoding="utf-8")
    output_dir = tmp_path / "out"

    class DummyGenerator:
        def __init__(self, *_, **__):
            pass

        def propose(self, prompt: str) -> dict:
            return {
                "id": "asset-1",
                "timestamp": "2025-01-01T00:00:00Z",
                "prompt": prompt,
                "provenance": {"agent": "GeneratorAgent"},
            }

    class DummyCritic:
        def __init__(self, *_, **__):
            pass

        def review(self, asset: dict) -> dict:
            return {
                "asset": asset,
                "issues": [],
                "ok": True,
                "reviewed_at": "2025-01-01T00:00:01Z",
                "validation_status": "passed",
                "mcp_response": {"status": "ok"},
            }

    monkeypatch.setattr(prompt_experiment, "GeneratorAgent", DummyGenerator)
    monkeypatch.setattr(prompt_experiment, "CriticAgent", DummyCritic)
    monkeypatch.setattr(prompt_experiment, "_ensure_validator", lambda: (lambda payload: {"status": "ok"}))

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
