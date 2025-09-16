"""Command line interface for running Synesthetic Labs agents."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from labs import CriticAgent, GeneratorAgent
from labs.lifecycle import run_pipeline


def _load_json(value: Optional[str]) -> Optional[Dict[str, Any]]:
    """Interpret *value* as JSON or path and return the loaded object."""
    if value is None:
        return None
    candidate = Path(value)
    try:
        if candidate.exists():
            with candidate.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        return json.loads(value)
    except OSError as exc:  # pragma: no cover - filesystem errors are unlikely in tests
        raise SystemExit(f"Failed to read {value}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON payload: {exc}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Synesthetic Labs agents")
    sub = parser.add_subparsers(dest="command", required=True)

    generate = sub.add_parser("generate", help="Run the generator agent")
    generate.add_argument("prompt_id", help="Identifier of the prompt to load")
    generate.add_argument(
        "--config",
        help="Inline JSON string or path containing generator configuration",
    )
    generate.add_argument(
        "--dataset-context",
        dest="dataset_context",
        help="Inline JSON or path describing dataset context",
    )

    critique = sub.add_parser("critique", help="Run the critic agent")
    critique.add_argument(
        "proposal",
        help="Inline JSON string or path pointing to a generator proposal",
    )

    pipeline = sub.add_parser("pipeline", help="Run generator and critic in sequence")
    pipeline.add_argument("prompt_id", help="Identifier of the prompt to load")
    pipeline.add_argument(
        "--config",
        help="Inline JSON string or path containing generator configuration",
    )
    pipeline.add_argument(
        "--dataset-context",
        dest="dataset_context",
        help="Inline JSON or path describing dataset context",
    )

    return parser


def run(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "generate":
        agent = GeneratorAgent()
        config = _load_json(args.config)
        dataset_context = _load_json(args.dataset_context)
        proposal = agent.propose(args.prompt_id, config=config, dataset_context=dataset_context)
        json.dump(proposal, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    if args.command == "critique":
        agent = CriticAgent()
        proposal_payload = _load_json(args.proposal)
        if proposal_payload is None:
            raise SystemExit("Proposal payload is required")
        review = agent.review(proposal_payload)
        json.dump(review, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    if args.command == "pipeline":
        generator = GeneratorAgent()
        critic = CriticAgent()
        config = _load_json(args.config)
        dataset_context = _load_json(args.dataset_context)
        review = run_pipeline(
            args.prompt_id,
            config=config,
            dataset_context=dataset_context,
            generator=generator,
            critic=critic,
        )
        json.dump(review, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    parser.error("No command provided")
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(run())
