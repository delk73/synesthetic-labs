"""Tests for the generator agent."""

from __future__ import annotations

import json

from labs.agents.generator import GeneratorAgent


def test_generator_propose_writes_log(tmp_path) -> None:
    log_path = tmp_path / "generator.jsonl"
    agent = GeneratorAgent(log_path=str(log_path))

    asset = agent.propose("synthwave pulse")

    for field in ("id", "timestamp", "prompt", "provenance"):
        assert field in asset

    assert asset["prompt"] == "synthwave pulse"
    assert asset["provenance"]["agent"] == "AssetAssembler"
    generator_info = asset["provenance"]["generator"]
    assert generator_info["agent"] == "GeneratorAgent"
    assert generator_info["version"] == "v0.1"
    assert asset["provenance"]["version"] == "v0.1"

    for section in ("shader", "tone", "haptic", "control", "meta"):
        assert section in asset
        assert asset[section]["component"] == section

    assert log_path.exists()
    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    logged = json.loads(lines[0])
    assert logged["id"] == asset["id"]
    assert logged["shader"]["component"] == "shader"
    assert logged["provenance"]["generator"]["agent"] == "GeneratorAgent"


def test_record_experiment_logs_experiment_path(tmp_path) -> None:
    log_path = tmp_path / "generator.jsonl"
    agent = GeneratorAgent(log_path=str(log_path))

    asset = {
        "id": "asset-123",
        "prompt": "synthwave pulse",
        "timestamp": "2024-01-01T00:00:00+00:00",
    }
    review = {
        "ok": True,
        "issues": [],
        "validation_status": "passed",
        "reviewed_at": "2024-01-01T00:00:10+00:00",
    }

    record = agent.record_experiment(
        asset=asset,
        review=review,
        experiment_path="meta/output/labs/experiments/asset-123.json",
    )

    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    logged = json.loads(lines[0])

    assert logged == record
    assert record["asset_id"] == "asset-123"
    assert record["experiment_path"] == "meta/output/labs/experiments/asset-123.json"
    assert record["validation"]["status"] == "passed"
