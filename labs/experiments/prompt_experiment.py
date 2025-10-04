"""Batch experiment runner for generator → critic prompts."""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Callable, Dict, List, Optional

from labs.agents.generator import GeneratorAgent
from labs.agents.critic import CriticAgent
from labs.logging import log_jsonl
from labs.mcp_stdio import build_validator_from_env


def _relativize(path: str) -> str:
    try:
        return os.path.relpath(path, start=os.getcwd())
    except ValueError:
        return path

def _load_prompts(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as handle:
        prompts = [line.strip() for line in handle]
    prompts = [prompt for prompt in prompts if prompt]
    if not prompts:
        raise ValueError("prompt file must contain at least one non-empty line")
    return prompts


def _ensure_validator() -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    return build_validator_from_env()


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run a batch of prompts through Synesthetic Labs")
    parser.add_argument("prompt_file", help="Path to a text file containing one prompt per line")
    parser.add_argument("output_dir", help="Directory to write per-run JSON and aggregated results")
    args = parser.parse_args(argv)

    prompts = _load_prompts(args.prompt_file)
    os.makedirs(args.output_dir, exist_ok=True)

    generator = GeneratorAgent()
    validator = _ensure_validator()
    critic = CriticAgent(validator=validator)

    schema_version = os.getenv("LABS_SCHEMA_VERSION", "0.7.3")

    total = len(prompts)
    ok_count = 0
    fail_count = 0

    results_log = os.path.join(args.output_dir, "all_results.jsonl")
    generated_dir = os.path.join(args.output_dir, "generated_assets")
    os.makedirs(generated_dir, exist_ok=True)
    validated_dir: Optional[str] = None

    for index, prompt in enumerate(prompts, start=1):
        asset = generator.propose(prompt, schema_version=schema_version)
        review = critic.review(asset)

        run_record = {
            "index": index,
            "prompt": prompt,
            "asset": asset,
            "review": review,
        }

        run_path = os.path.join(args.output_dir, f"run_{index}.json")
        with open(run_path, "w", encoding="utf-8") as handle:
            json.dump(run_record, handle, indent=2)
            handle.write("\n")

        asset_path = os.path.join(generated_dir, f"asset_{index}.json")
        with open(asset_path, "w", encoding="utf-8") as handle:
            json.dump(asset, handle, indent=2)
            handle.write("\n")

        experiment_path: Optional[str] = None

        if review.get("mcp_response"):
            if validated_dir is None:
                validated_dir = os.path.join(args.output_dir, "validated_assets")
                os.makedirs(validated_dir, exist_ok=True)
            validated_path = os.path.join(validated_dir, f"validated_{index}.json")
            with open(validated_path, "w", encoding="utf-8") as handle:
                json.dump(review["mcp_response"], handle, indent=2)
                handle.write("\n")
            experiment_path = _relativize(validated_path)

        try:
            generator.record_experiment(
                asset=asset,
                review=review,
                experiment_path=experiment_path,
            )
        except ValueError:
            pass

        log_jsonl(results_log, run_record)

        if review.get("ok"):
            ok_count += 1
        else:
            fail_count += 1

    print(f"Processed {total} prompts: {ok_count} ok, {fail_count} failed")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
