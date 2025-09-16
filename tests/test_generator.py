from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from labs.agents.generator import GeneratorAgent


def test_generator_produces_proposal_and_logs(tmp_path) -> None:
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    prompt_payload = {
        "task": "demo-asset",
        "objective": "Create a simple shader",
        "constraints": {"palette": "monochrome"},
    }
    (prompts_dir / "demo.json").write_text(json.dumps(prompt_payload), encoding="utf-8")
    output_path = tmp_path / "generator.log.jsonl"

    def fake_clock() -> datetime:
        return datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    def fake_id(seed: str) -> str:
        return hashlib.sha1(seed.encode("utf-8")).hexdigest()

    agent = GeneratorAgent(
        prompts_dir=prompts_dir,
        output_path=output_path,
        clock=fake_clock,
        id_factory=fake_id,
    )
    config = {"seed": 42}
    dataset_context = {"dataset": "demo"}

    proposal = agent.propose("demo", config=config, dataset_context=dataset_context)

    config_hash = hashlib.sha256(json.dumps(config, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    expected_seed = "|".join(["demo", "2024-01-01T12:00:00+00:00", config_hash])

    assert proposal["proposal_id"] == fake_id(expected_seed)
    assert proposal["prompt_id"] == "demo"
    assert proposal["asset"]["type"] == "demo-asset"
    assert proposal["asset"]["constraints"] == {"palette": "monochrome"}
    assert proposal["config"] == config
    assert Path(output_path).exists()

    log_lines = output_path.read_text(encoding="utf-8").strip().splitlines()
    assert log_lines, "generator log should contain at least one record"
    log_entry = json.loads(log_lines[-1])
    assert log_entry["event"] == "generator.propose"
    assert log_entry["proposal"]["proposal_id"] == proposal["proposal_id"]
