"""Tests for rating stubs logged by the critic."""

from __future__ import annotations

import json

from labs.agents.critic import CriticAgent


def test_critic_records_rating(tmp_path) -> None:
    log_path = tmp_path / "critic.jsonl"
    critic = CriticAgent(log_path=str(log_path))

    record = critic.record_rating(patch_id="patch-logger", rating={"score": 0.9}, asset_id="asset-x")

    assert record["patch_id"] == "patch-logger"
    assert record["rating"]["score"] == 0.9

    logged = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    assert logged[0]["type"] == "rating"
    assert logged[0]["asset_id"] == "asset-x"
