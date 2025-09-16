import json
from datetime import datetime, timezone
from pathlib import Path

from labs.agents.critic import Critic, CriticConfig
from labs.agents.generator import Generator, GeneratorConfig, PromptRepository
from labs.logging import FileLogSink


class FixedClock:
    def now(self):
        return datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


class StubMCPAdapter:
    def validate(self, payload):
        return {"passed": True, "details": {"parameters": payload.get("parameters")}}


def test_full_pipeline_writes_all_events(tmp_path: Path) -> None:
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    prompt_payload = {
        "task": "demo",
        "objective": "pipeline test",
    }
    (prompts_dir / "init.json").write_text(json.dumps(prompt_payload), encoding="utf-8")

    log_path = tmp_path / "run.jsonl"
    log_sink = FileLogSink(log_path)

    generator = Generator(PromptRepository(prompts_dir), log_sink=log_sink, clock=FixedClock())
    critic = Critic(StubMCPAdapter(), log_sink=log_sink)

    proposal = generator.generate(GeneratorConfig(prompt_id="init", prompt_parameters={"mode": "pipeline"}))
    critique = critic.review(proposal, CriticConfig())

    log_sink.write(
        {
            "event": "pipeline.completed",
            "proposal_id": proposal.proposal_id,
            "prompt_id": proposal.prompt_id,
            "recommended_action": critique.recommended_action,
            "mcp_passed": critique.mcp.passed,
        }
    )

    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 3
    final_event = json.loads(lines[-1])
    assert final_event["event"] == "pipeline.completed"
    assert final_event["recommended_action"] == critique.recommended_action
    assert final_event["mcp_passed"] is True

