"""Command line entry point for Synesthetic Labs."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, Optional

from labs.agents.generator import GeneratorAgent
from labs.agents.critic import CriticAgent, is_fail_fast_enabled
from labs.mcp_stdio import MCPUnavailableError, build_validator_from_env

_LOGGER = logging.getLogger("labs.cli")

_EXPERIMENTS_DIR_ENV = "LABS_EXPERIMENTS_DIR"
_DEFAULT_EXPERIMENTS_DIR = os.path.join("meta", "output", "labs", "experiments")
def _configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def _load_asset(value: str) -> Dict[str, Any]:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        with open(value, "r", encoding="utf-8") as handle:
            return json.load(handle)


def _experiments_dir() -> str:
    return os.getenv(_EXPERIMENTS_DIR_ENV, _DEFAULT_EXPERIMENTS_DIR)


def _persist_asset(asset: Dict[str, Any]) -> str:
    if "id" not in asset:
        raise ValueError("asset must include an 'id'")

    experiments_dir = _experiments_dir()
    os.makedirs(experiments_dir, exist_ok=True)

    path = os.path.join(experiments_dir, f"{asset['id']}.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(asset, handle, sort_keys=True, indent=2)
        handle.write("\n")
    return path


def _relativize(path: str) -> str:
    try:
        return os.path.relpath(path, start=os.getcwd())
    except ValueError:
        return path


def main(argv: Optional[list[str]] = None) -> int:
    """Entry point for the Labs CLI."""

    _configure_logging()

    parser = argparse.ArgumentParser(description="Synesthetic Labs CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate", help="Generate a proposal from a prompt")
    generate_parser.add_argument("prompt", help="Prompt text for the generator")

    critique_parser = subparsers.add_parser("critique", help="Critique a proposal JSON payload")
    critique_parser.add_argument("asset", help="JSON string or file path pointing to the asset")

    args = parser.parse_args(argv)

    if args.command == "generate":
        generator = GeneratorAgent()
        asset = generator.propose(args.prompt)

        try:
            validator_callback = build_validator_from_env()
        except MCPUnavailableError as exc:
            if is_fail_fast_enabled():
                _LOGGER.error("MCP unavailable: %s", exc)
                return 1
            _LOGGER.warning("Validation skipped: %s", exc)
            validator_callback = None

        critic = CriticAgent(validator=validator_callback)
        review = critic.review(asset)

        experiment_path: Optional[str] = None
        if review.get("ok"):
            persisted_path = _persist_asset(asset)
            experiment_path = _relativize(persisted_path)
        else:
            _LOGGER.error("Generation failed validation; asset not persisted")

        generator.record_experiment(
            asset=asset,
            review=review,
            experiment_path=experiment_path,
        )

        output_payload = {
            "asset": asset,
            "review": review,
            "experiment_path": experiment_path,
        }

        print(json.dumps(output_payload, indent=2))
        return 0 if review.get("ok") else 1

    if args.command == "critique":
        asset = _load_asset(args.asset)
        try:
            validator_callback = build_validator_from_env()
        except MCPUnavailableError as exc:
            if is_fail_fast_enabled():
                _LOGGER.error("MCP unavailable: %s", exc)
                return 1
            _LOGGER.warning("Validation skipped: %s", exc)
            validator_callback = None

        critic = CriticAgent(validator=validator_callback)
        review = critic.review(asset)
        print(json.dumps(review, indent=2))

        if not review.get("ok"):
            _LOGGER.error("Critique failed: MCP validation did not pass")
            return 1

        return 0

    parser.error("Unknown command")
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
