import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from labs.agents.generator import Generator, GeneratorConfig, PromptRepository
from labs.logging import FileLogSink


class FixedClock:
    def __init__(self) -> None:
        self._now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    def now(self) -> datetime:
        return self._now


@pytest.fixture
def prompts_dir(tmp_path: Path) -> Path:
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    payload = {
        "task": "demo",
        "objective": "exercise generator",
        "constraints": {"language": "python"},
    }
    (prompts / "init.json").write_text(json.dumps(payload), encoding="utf-8")
    return prompts


def test_generator_attaches_provenance_and_logs(tmp_path: Path, prompts_dir: Path) -> None:
    log_path = tmp_path / "run.jsonl"
    generator = Generator(
        PromptRepository(prompts_dir),
        log_sink=FileLogSink(log_path),
        clock=FixedClock(),
    )

    config = GeneratorConfig(prompt_id="init", prompt_parameters={"mode": "test"}, seed=7)
    proposal = generator.generate(config)

    assert proposal.prompt_id == "init"
    assert proposal.provenance["seed"] == 7
    assert proposal.payload["prompt"]["task"] == "demo"
    assert proposal.payload["parameters"] == {"mode": "test"}
    assert proposal.timestamp == "2024-01-01T12:00:00+00:00"
    assert proposal.provenance["prompt_path"].endswith("init.json")

    log_lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(log_lines) == 1
    assert "generator.proposal" in log_lines[0]


def test_missing_prompt_raises(prompts_dir: Path) -> None:
    generator = Generator(
        PromptRepository(prompts_dir),
        log_sink=FileLogSink(prompts_dir / "run.jsonl"),
        clock=FixedClock(),
    )

    with pytest.raises(FileNotFoundError):
        generator.generate(GeneratorConfig(prompt_id="unknown"))

