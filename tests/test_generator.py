"""Tests for the generator agent."""

from __future__ import annotations

import json

from labs.agents.generator import GeneratorAgent
from labs.mcp_stdio import resolve_mcp_endpoint


def test_generator_propose_writes_log(tmp_path) -> None:
    log_path = tmp_path / "generator.jsonl"
    agent = GeneratorAgent(log_path=str(log_path))

    asset = agent.propose("synthwave pulse", schema_version="0.7.4")

    for field in ("asset_id", "timestamp", "prompt", "provenance", "meta_info"):
        assert field in asset

    assert asset["prompt"] == "synthwave pulse"
    assert asset["provenance"]["agent"] == "AssetAssembler"
    generator_info = asset["provenance"]["generator"]
    assert generator_info["agent"] == "GeneratorAgent"
    assert generator_info["version"] == "v0.2"
    assert asset["provenance"]["version"] == "v0.2"
    assert asset["meta_info"]["provenance"]["trace_id"] == generator_info["trace_id"]

    for section in ("shader", "tone", "haptic"):
        assert section in asset
        assert "input_parameters" in asset[section]

    assert asset["$schema"].endswith("/0.7.4/synesthetic-asset.schema.json")
    assert "control_parameters" in asset["control"]
    assert isinstance(asset["modulations"], list)
    assert isinstance(asset["rule_bundle"], dict)

    assert log_path.exists()
    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    logged = json.loads(lines[0])
    assert logged["asset_id"] == asset["asset_id"]
    assert "input_parameters" in logged["shader"]
    assert logged["provenance"]["generator"]["agent"] == "GeneratorAgent"
    assert logged["trace_id"] == asset["meta_info"]["provenance"]["trace_id"]
    assert logged["mode"] == "local"
    assert isinstance(logged["strict"], bool)
    assert logged["transport"] == resolve_mcp_endpoint()
    assert logged["schema_version"] == "0.7.4"


def test_generator_propose_legacy_schema(tmp_path) -> None:
    log_path = tmp_path / "generator.jsonl"
    agent = GeneratorAgent(log_path=str(log_path))

    asset = agent.propose("legacy baseline", schema_version="0.7.3")

    assert asset["$schema"].endswith("/0.7.3/synesthetic-asset.schema.json")
    assert "name" in asset
    assert asset["name"]
    assert "controls" in asset and isinstance(asset["controls"], dict)
    assert isinstance(asset["controls"].get("mappings"), list)
    assert "meta_info" in asset and set(asset["meta_info"].keys()) == {"provenance"}
    assert asset["meta_info"]["provenance"]

    forbidden = {"asset_id", "timestamp", "prompt", "provenance", "modulations", "rule_bundle", "seed", "parameter_index", "control"}
    assert forbidden.isdisjoint(asset.keys())


def test_record_experiment_logs_experiment_path(tmp_path) -> None:
    log_path = tmp_path / "generator.jsonl"
    agent = GeneratorAgent(log_path=str(log_path))

    asset = {
        "asset_id": "asset-123",
        "prompt": "synthwave pulse",
        "timestamp": "2024-01-01T00:00:00+00:00",
        "meta_info": {
            "provenance": {"trace_id": "trace-123"}
        },
    }
    review = {
        "ok": True,
        "issues": [],
        "validation_status": "passed",
        "reviewed_at": "2024-01-01T00:00:10+00:00",
        "trace_id": "trace-123",
        "strict": True,
        "mode": "strict",
        "transport": "tcp",
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
    assert record["trace_id"] == "trace-123"
    assert record["mode"] == "strict"
    assert record["strict"] is True
    assert record["transport"] == "tcp"
