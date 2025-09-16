"""Command-line interface for the Synesthetic Labs agents."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
import sys
from typing import Any

from labs.agents import CriticAgent, GeneratorAgent


def build_parser() -> argparse.ArgumentParser:
    """Return the top-level argument parser."""

    parser = argparse.ArgumentParser(
        description="Run the Synesthetic Labs generator and critic agents."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser(
        "generate", help="Create a proposal from a prompt."
    )
    generate_parser.add_argument("prompt", help="Prompt text for the generator.")
    generate_parser.add_argument(
        "--log",
        type=Path,
        default=Path("meta/output/generator.jsonl"),
        help="Path to the JSONL file where generator events are appended.",
    )

    critique_parser = subparsers.add_parser(
        "critique", help="Review an existing generator proposal."
    )
    critique_parser.add_argument(
        "asset",
        help="Path to a JSON file containing the asset or '-' to read from stdin.",
    )
    critique_parser.add_argument(
        "--log",
        type=Path,
        default=Path("meta/output/critic.jsonl"),
        help="Path to the JSONL file where critic reviews are appended.",
    )

    return parser


def _load_asset(path: str) -> Any:
    if path == "-":
        return json.load(sys.stdin)
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main(argv: list[str] | None = None) -> int:
    """Entry point for the CLI."""

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "generate":
        agent = GeneratorAgent(log_path=args.log)
        proposal = agent.propose(args.prompt)
        json.dump(proposal, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    if args.command == "critique":
        asset = _load_asset(args.asset)
        agent = CriticAgent(log_path=args.log)
        review = agent.review(asset)
        json.dump(review, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    parser.error("Unknown command")
    return 2


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
