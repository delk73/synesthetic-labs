"""Tests for the critic agent."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from labs.agents.critic import CriticAgent


def test_critic_reports_missing_fields(tmp_path: Path) -> None:
    """Critic should flag assets that lack required metadata."""

    log_path = tmp_path / "critic_missing.jsonl"
    critic = CriticAgent(log_path=log_path)
    review = critic.review({"id": "example"})

    assert review["ok"] is False
    assert any(issue.startswith("Missing key") for issue in review["issues"])

    logged = [line for line in log_path.read_text(encoding="utf-8").splitlines() if line]
    assert len(logged) == 1
    record = json.loads(logged[0])
    assert record["ok"] is False
    assert record["asset_id"] == "example"


def test_valid_asset_passes_review(tmp_path: Path) -> None:
    """Critic should pass through assets that contain expected keys."""

    log_path = tmp_path / "critic_valid.jsonl"
    critic = CriticAgent(log_path=log_path)
    asset = {
        "id": "valid-asset",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prompt": "demo",
        "provenance": {"agent": "GeneratorAgent"},
    }
    review = critic.review(asset)

    assert review["ok"] is True
    assert review["issues"] == []
    assert review["prompt"] == asset["prompt"]

    logged = [line for line in log_path.read_text(encoding="utf-8").splitlines() if line]
    assert len(logged) == 1
    record = json.loads(logged[0])
    assert record["ok"] is True
    assert record["asset_id"] == "valid-asset"
