"""Command-line entry point for running the generator → critic loop."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from labs.agents.critic import Critic, CriticConfig
from labs.agents.generator import Generator, GeneratorConfig, PromptRepository
from labs.logging import FileLogSink


class PassthroughMCPAdapter:
    """Default MCP adapter stub that accepts every payload."""

    def validate(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:  # pragma: no cover - trivial
        _ = payload
        return {"passed": True, "details": {"adapter": "passthrough"}}


def _default_log_path(output_dir: Path) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return output_dir / f"run_{timestamp}.jsonl"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Synesthetic Labs generator → critic loop.")
    parser.add_argument(
        "--prompt-id",
        default="init",
        help="Prompt identifier (file stem under meta/prompts) to seed the generator.",
    )
    parser.add_argument(
        "--prompts-dir",
        default="meta/prompts",
        type=Path,
        help="Directory containing generator prompt JSON files.",
    )
    parser.add_argument(
        "--output-dir",
        default="meta/output",
        type=Path,
        help="Directory where structured logs are written.",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        default=None,
        help="Optional explicit log file path (overrides timestamped default).",
    )
    parser.add_argument(
        "--seed",
        default=0,
        type=int,
        help="Seed value for deterministic generator outputs.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    prompts_dir: Path = args.prompts_dir
    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = args.log_file or _default_log_path(output_dir)

    log_sink = FileLogSink(log_path)
    prompt_repository = PromptRepository(prompts_dir)
    generator = Generator(prompt_repository, log_sink=log_sink)
    critic = Critic(PassthroughMCPAdapter(), log_sink=log_sink)

    generator_config = GeneratorConfig(
        prompt_id=args.prompt_id,
        seed=args.seed,
        prompt_parameters={"seed": args.seed},
    )
    proposal = generator.generate(generator_config)
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

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())

