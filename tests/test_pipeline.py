from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from labs.agents.critic import CriticAgent
from labs.agents.generator import GeneratorAgent
from labs.lifecycle import run_pipeline


def test_generator_critic_pipeline(tmp_path) -> None:
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    prompt_payload = {
        "task": "tone",
        "objective": "Generate a calming tone",
        "constraints": {"duration": 3},
    }
    (prompts_dir / "tone.json").write_text(json.dumps(prompt_payload), encoding="utf-8")

    def gen_clock() -> datetime:
        return datetime(2024, 1, 3, 9, 30, 0, tzinfo=timezone.utc)

    def critic_clock() -> datetime:
        return datetime(2024, 1, 3, 9, 31, 0, tzinfo=timezone.utc)

    def fake_id(seed: str) -> str:
        return hashlib.md5(seed.encode("utf-8")).hexdigest()

    generator = GeneratorAgent(
        prompts_dir=prompts_dir,
        output_path=tmp_path / "generator.log.jsonl",
        clock=gen_clock,
        id_factory=fake_id,
    )

    config_hash = hashlib.sha256(json.dumps({}, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    expected_seed = "|".join(["tone", "2024-01-03T09:30:00+00:00", config_hash])
    expected_id = fake_id(expected_seed)

    def validator(payload):
        assert payload["proposal_id"] == expected_id
        return {"passed": True, "status": "ok"}

    critic = CriticAgent(
        output_path=tmp_path / "critic.log.jsonl",
        clock=critic_clock,
        mcp_validator=validator,
    )

    pipeline_log = tmp_path / "pipeline.log.jsonl"

    review = run_pipeline(
        "tone",
        generator=generator,
        critic=critic,
        log_path=pipeline_log,
    )

    assert review["proposal"]["proposal_id"] == expected_id
    assert review["ok"] is True
    assert review["validation"]["passed"] is True
    assert review["critique"]["recommendations"] == ["ready for MCP submission"]
    assert (tmp_path / "generator.log.jsonl").exists()
    assert (tmp_path / "critic.log.jsonl").exists()
    assert pipeline_log.exists()
    log_entry = json.loads(pipeline_log.read_text(encoding="utf-8").strip().splitlines()[-1])
    assert log_entry["event"] == "pipeline.run"
    assert log_entry["result"]["ok"] is True
