"""End-to-end generator pipeline tests."""

from __future__ import annotations

import json

from labs.agents.critic import CriticAgent
from labs.generator import AssetAssembler
from labs.logging import log_jsonl


def test_asset_assembler_end_to_end(tmp_path) -> None:
    assembler = AssetAssembler(schema_version="0.7.4")
    asset = assembler.generate("e2e wiring test", seed=1234, schema_version="0.7.4")

    output_dir = tmp_path / "meta" / "output" / "test_generator"
    output_dir.mkdir(parents=True, exist_ok=True)

    asset_path = output_dir / "asset.json"
    asset_path.write_text(json.dumps(asset, indent=2), encoding="utf-8")

    log_path = output_dir / "assets.jsonl"
    log_jsonl(str(log_path), asset)

    recorded_targets = []

    def validator(payload: dict) -> dict:
        recorded_targets.append(payload["asset_id"])
        return {"status": "ok", "asset_id": payload["asset_id"]}

    critic_log = output_dir / "critic.jsonl"
    critic = CriticAgent(validator=validator, log_path=str(critic_log))
    review = critic.review(asset)

    assert recorded_targets == [asset["asset_id"]]
    assert review["ok"] is True
    assert review["validation_status"] == "passed"
    assert asset_path.exists()
    assert log_path.exists()
    assert critic_log.exists()
    assert log_path.read_text(encoding="utf-8").strip()
