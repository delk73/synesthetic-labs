"""Command line entry point for Synesthetic Labs."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from typing import Any, Callable, Dict, Optional

from labs.agents.critic import CriticAgent, is_fail_fast_enabled
from labs.agents.generator import GeneratorAgent
from labs.generator.assembler import AssetAssembler
from labs.generator.external import ExternalGenerationError, build_external_generator
from labs.mcp_stdio import MCPUnavailableError, build_validator_from_env
from labs.patches import apply_patch, preview_patch, rate_patch

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
    if "asset_id" not in asset:
        raise ValueError("asset must include an 'asset_id'")

    experiments_dir = _experiments_dir()
    os.makedirs(experiments_dir, exist_ok=True)

    path = os.path.join(experiments_dir, f"{asset['asset_id']}.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(asset, handle, sort_keys=True, indent=2)
        handle.write("\n")
    return path


def _relativize(path: str) -> str:
    try:
        return os.path.relpath(path, start=os.getcwd())
    except ValueError:
        return path


def _build_validator_optional() -> Optional[Callable[[Dict[str, Any]], Dict[str, Any]]]:
    try:
        return build_validator_from_env()
    except MCPUnavailableError as exc:
        if is_fail_fast_enabled():
            raise
        _LOGGER.warning("Validation warning; continuing with degraded MCP validation: %s", exc)

        def _degraded_validator(payload: Dict[str, Any]) -> Dict[str, Any]:
            validator = build_validator_from_env()
            return validator(payload)

        return _degraded_validator


def main(argv: Optional[list[str]] = None) -> int:
    """Entry point for the Labs CLI."""

    _configure_logging()

    parser = argparse.ArgumentParser(description="Synesthetic Labs CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate", help="Generate a proposal from a prompt")
    generate_parser.add_argument("prompt", help="Prompt text for the generator")
    generate_parser.add_argument(
        "--engine",
        choices=("gemini", "openai", "deterministic"),
        help="Optional external engine to fulfil the prompt",
    )
    generate_parser.add_argument(
        "--schema-version",
        type=str,
        default=os.getenv("LABS_SCHEMA_VERSION", AssetAssembler.DEFAULT_SCHEMA_VERSION),
        help=f"Target schema version (default: {AssetAssembler.DEFAULT_SCHEMA_VERSION})",
    )
    generate_parser.add_argument("--seed", type=int, help="Optional random seed for generation")
    generate_parser.add_argument("--temperature", type=float, help="Temperature override for external engines")
    generate_parser.add_argument("--timeout-s", dest="timeout_s", type=int, help="Override external call timeout (seconds)")
    strict_group = generate_parser.add_mutually_exclusive_group()
    strict_group.add_argument("--strict", dest="strict", action="store_true", help="Fail-fast when MCP validation is unavailable")
    strict_group.add_argument("--relaxed", dest="strict", action="store_false", help="Downgrade MCP outages to warnings")
    generate_parser.set_defaults(strict=None)

    critique_parser = subparsers.add_parser("critique", help="Critique a proposal JSON payload")
    critique_parser.add_argument("asset", help="JSON string or file path pointing to the asset")

    preview_parser = subparsers.add_parser("preview", help="Preview a patch against an asset")
    preview_parser.add_argument("asset", help="JSON string or file path pointing to the asset")
    preview_parser.add_argument("patch", help="JSON string or file path pointing to the patch payload")

    apply_parser = subparsers.add_parser("apply", help="Apply a patch and validate the result")
    apply_parser.add_argument("asset", help="JSON string or file path pointing to the asset")
    apply_parser.add_argument("patch", help="JSON string or file path pointing to the patch payload")

    rate_parser = subparsers.add_parser("rate", help="Record a rating stub for a patch")
    rate_parser.add_argument("patch_id", help="Identifier of the patch being rated")
    rate_parser.add_argument("rating", help="JSON string or file path pointing to the rating payload")
    rate_parser.add_argument("--asset-id", dest="asset_id", help="Optional asset identifier linked to the rating")

    args = parser.parse_args(argv)

    if args.command == "generate":
        engine = getattr(args, "engine", None)
        generator: Optional[GeneratorAgent] = None
        external_context: Optional[Dict[str, Any]] = None

        if args.strict is not None:
            os.environ["LABS_FAIL_FAST"] = "1" if args.strict else "0"

        if engine and engine != "deterministic":
            external_generator = build_external_generator(engine)
            external_parameters: Dict[str, Any] = {}
            if args.temperature is not None:
                external_parameters["temperature"] = args.temperature
            timeout_value = float(args.timeout_s) if args.timeout_s is not None else None
            try:
                asset, external_context = external_generator.generate(
                    args.prompt,
                    parameters=external_parameters or None,
                    seed=args.seed,
                    timeout=timeout_value,
                    schema_version=args.schema_version,
                )
            except ExternalGenerationError as exc:
                external_generator.record_failure(exc)
                _LOGGER.error("External generator %s failed: %s", engine, exc)
                return 1
        else:
            generator = GeneratorAgent(schema_version=args.schema_version)
            asset = generator.propose(
                args.prompt, seed=args.seed, schema_version=args.schema_version
            )

        try:
            validator_callback = _build_validator_optional()
        except MCPUnavailableError as exc:
            _LOGGER.error("MCP unavailable: %s", exc)
            return 1

        critic = CriticAgent(validator=validator_callback)
        review = critic.review(asset)

        experiment_path: Optional[str] = None
        if review.get("ok") and review.get("mcp_response", {}).get("ok"):
            if "asset_id" in asset:
                persisted_path = _persist_asset(asset)
                experiment_path = _relativize(persisted_path)
            else:
                _LOGGER.warning("Asset lacks asset_id; skipping persistence")
        else:
            _LOGGER.error("Generation failed validation; asset not persisted")

        if engine and external_context is not None:
            external_generator.record_run(
                context=external_context,
                review=review,
                experiment_path=experiment_path,
            )
        elif generator is not None:
            if "asset_id" in asset:
                generator.record_experiment(
                    asset=asset,
                    review=review,
                    experiment_path=experiment_path,
                )
            else:
                _LOGGER.warning("Skipping experiment log; asset lacks asset_id")

        output_payload = {
            "asset": asset,
            "review": review,
            "experiment_path": experiment_path,
        }

        if engine and engine != "deterministic":
            output_payload["engine"] = engine

        print(json.dumps(output_payload, indent=2))
        return 0 if review.get("ok") and review.get("mcp_response", {}).get("ok") else 1

    if args.command == "critique":
        asset = _load_asset(args.asset)
        try:
            validator_callback = _build_validator_optional()
        except MCPUnavailableError as exc:
            _LOGGER.error("MCP unavailable: %s", exc)
            return 1

        critic = CriticAgent(validator=validator_callback)
        review = critic.review(asset)
        print(json.dumps(review, indent=2))

        if not review.get("ok"):
            _LOGGER.error("Critique failed: MCP validation did not pass")
            return 1

        return 0

    if args.command == "preview":
        asset = _load_asset(args.asset)
        patch = _load_asset(args.patch)
        record = preview_patch(asset, patch)
        print(json.dumps(record, indent=2))
        return 0

    if args.command == "apply":
        asset = _load_asset(args.asset)
        patch = _load_asset(args.patch)

        try:
            validator_callback = _build_validator_optional()
        except MCPUnavailableError as exc:
            _LOGGER.error("MCP unavailable: %s", exc)
            return 1

        critic = CriticAgent(validator=validator_callback)
        result = apply_patch(asset, patch, critic=critic)
        print(json.dumps(result, indent=2))
        return 0 if result["review"].get("ok") else 1

    if args.command == "rate":
        rating_payload = _load_asset(args.rating)
        record = rate_patch(args.patch_id, rating_payload, asset_id=args.asset_id)
        print(json.dumps(record, indent=2))
        return 0

    parser.error("Unknown command")
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
