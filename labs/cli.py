"""Command line entry point for Synesthetic Labs."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from typing import Any, Callable, Dict, Optional

from dotenv import load_dotenv


def _load_env_file(path: str | None = None) -> None:
    """Load environment variables using python-dotenv and enforce required keys."""

    env_path = path or os.path.join(os.path.dirname(__file__), "..", ".env")
    load_dotenv(dotenv_path=env_path)

    raw_engine = os.getenv("LABS_EXTERNAL_ENGINE")
    raw_external_live = os.getenv("LABS_EXTERNAL_LIVE")

    os.environ.setdefault("LABS_SCHEMA_VERSION", "0.7.3")
    os.environ.setdefault("LABS_FAIL_FAST", os.getenv("LABS_FAIL_FAST", "1"))
    os.environ.setdefault("LABS_EXTERNAL_ENGINE", raw_engine or "azure")
    os.environ.setdefault("LABS_EXTERNAL_LIVE", raw_external_live or "0")
    os.environ.setdefault("GEMINI_MODEL", os.getenv("GEMINI_MODEL", "gemini-2.0-flash"))

    logger = logging.getLogger("labs.cli")
    engine = os.environ.get("LABS_EXTERNAL_ENGINE", "azure").strip().lower()

    if not raw_engine:
        logger.warning("LABS_EXTERNAL_ENGINE not set; defaulting to '%s'", engine)
    if not raw_external_live:
        logger.warning("LABS_EXTERNAL_LIVE not set; defaulting to mock mode (0)")

    azure_keys = (
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_DEPLOYMENT",
        "AZURE_OPENAI_API_VERSION",
    )
    gemini_keys = (
        "GEMINI_API_KEY",
        "GEMINI_MODEL",
        "GEMINI_ENDPOINT",
    )

    required_keys = azure_keys if engine == "azure" else gemini_keys if engine == "gemini" else ()
    for required_key in required_keys:
        if not os.getenv(required_key):
            logger.warning("Missing required env var for %s engine: %s", engine, required_key)


_load_env_file()

_LOGGER = logging.getLogger("labs.cli")

_MANDATORY_ENV_VARS = ("LABS_EXTERNAL_LIVE",)
for _env_var in _MANDATORY_ENV_VARS:
    if not os.getenv(_env_var):
        _LOGGER.warning("Missing environment variable %s; falling back to mock mode.", _env_var)

_ENGINE_ENV_VARS = {
    "azure": ("AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_DEPLOYMENT", "AZURE_OPENAI_API_VERSION"),
    "gemini": ("GEMINI_API_KEY", "GEMINI_MODEL", "GEMINI_ENDPOINT"),
}
_active_engine = os.getenv("LABS_EXTERNAL_ENGINE", "azure").strip().lower()
for _env_var in _ENGINE_ENV_VARS.get(_active_engine, ()):  # pragma: no branch - trivial iteration
    if not os.getenv(_env_var):
        _LOGGER.warning(
            "Missing environment variable %s for %s engine; falling back to mock mode.",
            _env_var,
            _active_engine,
        )

from labs.agents.critic import CriticAgent, is_fail_fast_enabled
from labs.agents.generator import GeneratorAgent
from labs.generator.assembler import AssetAssembler
from labs.generator.external import ExternalGenerationError, build_external_generator
from labs.mcp import MCPClient, MCPClientError, MCPValidationError
from labs.mcp_stdio import MCPUnavailableError, build_validator_from_env
from labs.patches import apply_patch, preview_patch, rate_patch

_EXPERIMENTS_DIR_ENV = "LABS_EXPERIMENTS_DIR"
_DEFAULT_EXPERIMENTS_DIR = os.path.join("meta", "output", "labs", "experiments")
_DEFAULT_MCP_LOG_PATH = os.path.join("meta", "output", "labs", "mcp.jsonl")
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

    telemetry_path = os.getenv("LABS_MCP_LOG_PATH") or _DEFAULT_MCP_LOG_PATH
    os.environ.setdefault("LABS_MCP_LOG_PATH", telemetry_path)
    requested_version = getattr(args, "schema_version", None)

    try:
        mcp_client = MCPClient(
            schema_version=requested_version,
            resolution=os.getenv("LABS_SCHEMA_RESOLUTION"),
            telemetry_path=telemetry_path,
        )
    except MCPClientError as exc:
        _LOGGER.error("Failed to initialise MCP client: %s", exc)
        return 1

    mcp_client.record_event(
        "cli_ready",
        command=args.command,
        schema_version=mcp_client.schema_version,
        schema_resolution=mcp_client.resolution,
    )

    def _complete(status: int) -> int:
        mcp_client.record_event(
            "cli_shutdown",
            command=args.command,
            exit_code=status,
        )
        return status

    if args.command == "generate":
        engine = getattr(args, "engine", None)
        generator: Optional[GeneratorAgent] = None
        external_context: Optional[Dict[str, Any]] = None

        if args.strict is not None:
            os.environ["LABS_FAIL_FAST"] = "1" if args.strict else "0"

        try:
            mcp_client.fetch_schema(version=args.schema_version)
        except MCPClientError as exc:
            _LOGGER.error("Failed to fetch schema via MCP: %s", exc)
            return _complete(1)

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
                return _complete(1)
        else:
            generator = GeneratorAgent(schema_version=args.schema_version)
            asset = generator.propose(
                args.prompt, seed=args.seed, schema_version=args.schema_version
            )

        try:
            validator_callback = _build_validator_optional()
        except MCPUnavailableError as exc:
            _LOGGER.error("MCP unavailable: %s", exc)
            return _complete(1)

        critic = CriticAgent(validator=validator_callback)
        review = critic.review(asset)

        strict_flag = bool(args.strict if args.strict is not None else is_fail_fast_enabled())
        strict_failure = False
        prior_mcp_response = review.get("mcp_response") if isinstance(review.get("mcp_response"), dict) else None
        try:
            mcp_response = mcp_client.confirm(asset, strict=strict_flag)
        except MCPValidationError as exc:
            result_payload = exc.result if isinstance(exc.result, dict) else None
            mcp_response = result_payload or {"ok": False, "reason": "validation_failed"}
            strict_failure = True
        except MCPClientError as exc:
            mcp_response = {
                "ok": False,
                "reason": "mcp_client_error",
                "detail": str(exc),
            }
            strict_failure = True

        review.setdefault("mode", "strict" if strict_flag else "relaxed")
        review["mcp_response_local"] = mcp_response

        def _response_ok(payload: Optional[Dict[str, Any]]) -> bool:
            if not isinstance(payload, dict):
                return False
            if "ok" in payload:
                return bool(payload.get("ok"))
            status = payload.get("status")
            if isinstance(status, str):
                return status.lower() in {"ok", "passed", "pass", "success"}
            return False

        prior_ok = True
        if prior_mcp_response is not None:
            review.setdefault("mcp_response", prior_mcp_response)
            prior_ok = _response_ok(prior_mcp_response)
        else:
            review["mcp_response"] = mcp_response

        local_ok = _response_ok(mcp_response)
        mcp_ok = prior_ok and local_ok
        relaxed_mode = _is_relaxed_mode(review)

        if mcp_ok:
            _LOGGER.info("MCP validation passed in %s mode", review.get("mode", "strict"))
        elif relaxed_mode:
            _LOGGER.warning("MCP validation failed in relaxed mode; emitting degraded result")
        else:
            _LOGGER.error("MCP validation failed in strict mode; asset not persisted")
            strict_failure = True

        experiment_path: Optional[str] = None
        if mcp_ok:
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
        return _complete(exit_code)

    if args.command == "critique":
        asset = _load_asset(args.asset)
        try:
            validator_callback = _build_validator_optional()
        except MCPUnavailableError as exc:
            _LOGGER.error("MCP unavailable: %s", exc)
            return _complete(1)

        critic = CriticAgent(validator=validator_callback)
        review = critic.review(asset)
        print(json.dumps(review, indent=2))

        if not _review_mcp_ok(review):
            if _is_relaxed_mode(review):
                _LOGGER.warning("Critique completed in relaxed mode despite MCP failure")
            else:
                _LOGGER.error("Critique failed: MCP validation did not pass")
            return _complete(1)

        return _complete(0)

    if args.command == "preview":
        asset = _load_asset(args.asset)
        patch = _load_asset(args.patch)
        record = preview_patch(asset, patch)
        print(json.dumps(record, indent=2))
        return _complete(0)

    if args.command == "apply":
        asset = _load_asset(args.asset)
        patch = _load_asset(args.patch)

        try:
            validator_callback = _build_validator_optional()
        except MCPUnavailableError as exc:
            _LOGGER.error("MCP unavailable: %s", exc)
            return _complete(1)

        critic = CriticAgent(validator=validator_callback)
        result = apply_patch(asset, patch, critic=critic)
        print(json.dumps(result, indent=2))

        review_payload = result["review"]
        if _review_mcp_ok(review_payload):
            return _complete(0)
        if _is_relaxed_mode(review_payload):
            _LOGGER.warning("Patch applied in relaxed mode; emitting degraded result")
            return _complete(1)
        return _complete(1)

    if args.command == "rate":
        rating_payload = _load_asset(args.rating)
        record = rate_patch(args.patch_id, rating_payload, asset_id=args.asset_id)
        print(json.dumps(record, indent=2))
        return _complete(0)

    _complete(2)
    parser.error("Unknown command")
    return _complete(1)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
