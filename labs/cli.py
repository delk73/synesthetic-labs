"""Command-line interface for Synesthetic Labs agents."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

from labs.agents.critic import CriticAgent
from labs.agents.generator import GeneratorAgent

LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Construct the argument parser with generator and critic subcommands."""

    parser = argparse.ArgumentParser(
        description="Run Synesthetic Labs generator and critic agents."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser(
        "generate", help="Generate a proposal from a text prompt."
    )
    generate_parser.add_argument("prompt", help="Prompt text for the generator.")
    generate_parser.add_argument(
        "--log",
        default="meta/output/proposals.jsonl",
        help="Destination JSONL file for generated proposals.",
    )

    critique_parser = subparsers.add_parser(
        "critique", help="Critique a previously generated proposal."
    )
    critique_parser.add_argument(
        "asset",
        help="Path to a JSON file containing the asset to review, or '-' for stdin.",
    )
    critique_parser.add_argument(
        "--log",
        default="meta/output/reviews.jsonl",
        help="Destination JSONL file for recorded reviews.",
    )

    return parser


def _load_asset(path: str) -> dict[str, Any]:
    """Load an asset from a file path or stdin."""

    if path == "-":
        data = sys.stdin.read()
    else:
        data = Path(path).read_text(encoding="utf-8")
    return json.loads(data)


def main(argv: list[str] | None = None) -> int:
    """Entry point for the CLI."""

    logging.basicConfig(level=logging.INFO)
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "generate":
        agent = GeneratorAgent(log_path=args.log)
        record = agent.propose(args.prompt)
        json.dump(record, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
        LOGGER.debug("Proposal emitted to stdout")
        return 0

    if args.command == "critique":
        asset = _load_asset(args.asset)
        agent = CriticAgent(log_path=args.log)
        review = agent.review(asset)
        json.dump(review, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
        LOGGER.debug("Review emitted to stdout")
        return 0

    parser.error("Unknown command")
    return 2


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
