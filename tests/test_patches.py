"""Patch lifecycle stub tests."""

from __future__ import annotations

import json

from labs.agents.critic import CriticAgent
from labs.patches import apply_patch, preview_patch, rate_patch


def test_preview_patch_logs(tmp_path) -> None:
    log_path = tmp_path / "patches.jsonl"
    asset = {"id": "asset-1"}
    patch = {"id": "patch-1", "updates": {"meta": {"title": "Updated"}}}

    record = preview_patch(asset, patch, log_path=str(log_path))

    assert record["patch_id"] == "patch-1"
    assert log_path.exists()
    logged = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    assert logged[0]["action"] == "preview"
    assert logged[0]["changes"] == patch["updates"]


def test_apply_patch_runs_critic(tmp_path) -> None:
    log_path = tmp_path / "patches.jsonl"
    critic_log = tmp_path / "critic.jsonl"

    def validator(payload: dict) -> dict:
        return {"status": "ok", "asset_id": payload["id"]}

    critic = CriticAgent(validator=validator, log_path=str(critic_log))

    asset = {
        "id": "asset-2",
        "meta": {"title": "Original"},
        "timestamp": "2024-01-01T00:00:00+00:00",
        "prompt": "baseline",
        "provenance": {"agent": "GeneratorAgent"},
    }
    patch = {"id": "patch-2", "updates": {"meta": {"title": "Patched"}}}

    result = apply_patch(asset, patch, critic=critic, log_path=str(log_path))

    assert result["asset"]["meta"] == {"title": "Patched"}
    assert result["review"]["ok"] is True
    assert result["review"]["patch_id"] == "patch-2"

    logged = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    assert logged[0]["action"] == "apply"
    assert logged[0]["review"]["validation_status"] == "passed"


def test_rate_patch_logs_rating(tmp_path) -> None:
    log_path = tmp_path / "patches.jsonl"
    critic_log = tmp_path / "critic.jsonl"
    critic = CriticAgent(log_path=str(critic_log))

    record = rate_patch(
        "patch-3",
        {"score": 0.75},
        asset_id="asset-3",
        critic=critic,
        log_path=str(log_path),
    )

    assert record["rating"]["score"] == 0.75
    assert record["critic_record"]["patch_id"] == "patch-3"

    logged = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    assert logged[0]["action"] == "rate"
    assert logged[0]["patch_id"] == "patch-3"

    critic_logged = [json.loads(line) for line in critic_log.read_text(encoding="utf-8").splitlines()]
    assert critic_logged[0]["type"] == "rating"
    assert critic_logged[0]["patch_id"] == "patch-3"
