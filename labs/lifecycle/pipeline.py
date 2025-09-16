"""Pipeline orchestration helpers for generator → critic runs."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from labs.agents import CriticAgent, GeneratorAgent
from labs.logging import log_jsonl

Proposal = Dict[str, Any]
ReviewPackage = Dict[str, Any]


DEFAULT_PIPELINE_LOG = Path("meta/output/pipeline.log.jsonl")


def run_pipeline(
    prompt_id: str,
    *,
    config: Optional[Dict[str, Any]] = None,
    dataset_context: Optional[Dict[str, Any]] = None,
    generator: Optional[GeneratorAgent] = None,
    critic: Optional[CriticAgent] = None,
    log_path: Path | str = DEFAULT_PIPELINE_LOG,
) -> ReviewPackage:
    """Execute a generator → critic pass and log the combined artefact.

    Parameters
    ----------
    prompt_id:
        Prompt identifier passed to the generator agent.
    config:
        Optional generator configuration payload.
    dataset_context:
        Optional dataset metadata forwarded to the generator.
    generator:
        Pre-configured generator instance. When omitted a default instance is created.
    critic:
        Pre-configured critic instance. When omitted a default instance is created.
    log_path:
        Location where the combined pipeline record should be appended.
    """

    generator_agent = generator or GeneratorAgent()
    critic_agent = critic or CriticAgent()

    proposal: Proposal = generator_agent.propose(
        prompt_id,
        config=config,
        dataset_context=dataset_context,
    )
    review: ReviewPackage = critic_agent.review(proposal)

    log_jsonl(log_path, {"event": "pipeline.run", "result": review})
    return review


__all__ = ["run_pipeline", "DEFAULT_PIPELINE_LOG"]
