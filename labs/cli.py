"""Command line entry point for Synesthetic Labs."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from typing import Any, Callable, Dict, Optional

from dotenv import load_dotenv
from jsonschema import ValidationError


def _load_env_file(path: str | None = None) -> None:
    """Load environment variables using python-dotenv and surface required knobs."""

    env_path = path or os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv()

    defaults = {
        "LABS_SCHEMA_VERSION": "0.7.3",
        "LABS_FAIL_FAST": "1",
        "LABS_EXTERNAL_ENGINE": os.getenv("LABS_EXTERNAL_ENGINE", "gemini"),
        "GEMINI_MODEL": os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
        "AZURE_OPENAI_API_VERSION": os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
    }
    for key, value in defaults.items():
        os.environ.setdefault(key, value)

    logger = logging.getLogger("labs.cli")
    required_keys = (
        "GEMINI_API_KEY",
        "LABS_EXTERNAL_LIVE",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_DEPLOYMENT",
    )
    for required_key in required_keys:
        if not os.getenv(required_key):
            logger.warning("Missing required env var: %s", required_key)


_load_env_file()

_LOGGER = logging.getLogger("labs.cli")

for _env_var in (
    "LABS_EXTERNAL_LIVE",
    "LABS_EXTERNAL_ENGINE",
    "GEMINI_API_KEY",
    "OPENAI_API_KEY",
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_DEPLOYMENT",
):
    if not os.getenv(_env_var):
        _LOGGER.warning("Missing environment variable %s; falling back to mock mode.", _env_var)

from labs.agents.critic import CriticAgent, is_fail_fast_enabled
from labs.agents.generator import GeneratorAgent
from labs.generator.assembler import AssetAssembler
from labs.generator.external import ExternalGenerationError, build_external_generator
from labs.mcp.validate import invoke_mcp
from labs.mcp_stdio import MCPUnavailableError, build_validator_from_env
from labs.patches import apply_patch, preview_patch, rate_patch

_EXPERIMENTS_DIR_ENV = "LABS_EXPERIMENTS_DIR"
_DEFAULT_EXPERIMENTS_DIR = os.path.join("meta", "output", "labs", "experiments")
def _configure_logging() -> None:
    log_level = os.getenv("LABS_LOG_LEVEL", "INFO")
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


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


def _review_mcp_ok(review: Dict[str, Any]) -> bool:
    mcp_response = review.get("mcp_response")
    if isinstance(mcp_response, dict) and "ok" in mcp_response:
        return bool(mcp_response.get("ok"))
    return bool(review.get("ok"))


def _is_relaxed_mode(review: Dict[str, Any]) -> bool:
    return review.get("mode") == "relaxed"


def main(argv: Optional[list[str]] = None) -> int:
    """Entry point for the Labs CLI."""

    _configure_logging()

    parser = argparse.ArgumentParser(description="Synesthetic Labs CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate", help="Generate a proposal from a prompt")
    generate_parser.add_argument("prompt", help="Prompt text for the generator")
    generate_parser.add_argument(
        "--engine",
        choices=("gemini", "openai", "azure", "deterministic"),
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

        strict_flag = args.strict if args.strict is not None else is_fail_fast_enabled()

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

        precomputed_mcp = review.get("mcp_response") if isinstance(review.get("mcp_response"), dict) else None

        strict_failure = False
        try:
            mcp_result = invoke_mcp(
                asset,
                strict=strict_flag,
                validator=validator_callback,
                result=precomputed_mcp,
            )
        except ValidationError as exc:
            strict_failure = True
            _LOGGER.error("MCP validation failed in strict mode; asset not persisted: %s", exc)
            mcp_result = precomputed_mcp or {
                "ok": False,
                "reason": "validation_failed",
                "detail": str(exc),
            }

        review["mcp_response"] = mcp_result
        review["strict"] = strict_flag
        review["mode"] = "strict" if strict_flag else "relaxed"
        review["ok"] = bool(mcp_result.get("ok"))

        mcp_ok = review["ok"]
        relaxed_mode = not strict_flag

        if mcp_ok:
            _LOGGER.info("MCP validation passed in %s mode", review.get("mode", "strict"))
        elif relaxed_mode and not strict_failure:
            _LOGGER.warning("MCP validation failed in relaxed mode; emitting degraded result")
        else:
            _LOGGER.error("MCP validation failed in strict mode; asset not persisted")
            strict_failure = True

        experiment_path: Optional[str] = None
        should_persist = (mcp_ok or relaxed_mode) and not strict_failure
        if should_persist:
            if "asset_id" in asset:
                persisted_path = _persist_asset(asset)
                experiment_path = _relativize(persisted_path)
            else:
                _LOGGER.warning("Asset lacks asset_id; skipping persistence")

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
        exit_code = 0 if mcp_ok else 1
        if strict_failure:
            sys.exit(exit_code)
        return exit_code

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

        if not _review_mcp_ok(review):
            if _is_relaxed_mode(review):
                _LOGGER.warning("Critique completed in relaxed mode despite MCP failure")
            else:
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

        review_payload = result["review"]
        if _review_mcp_ok(review_payload):
            return 0
        if _is_relaxed_mode(review_payload):
            _LOGGER.warning("Patch applied in relaxed mode; emitting degraded result")
            return 1
        return 1

    if args.command == "rate":
        rating_payload = _load_asset(args.rating)
        record = rate_patch(args.patch_id, rating_payload, asset_id=args.asset_id)
        print(json.dumps(record, indent=2))
        return 0

    parser.error("Unknown command")
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
