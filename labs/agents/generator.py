"""Generator agent responsible for assembling proposals for critic review."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Protocol
import uuid

from labs.logging import LogSink, NullLogSink


class Clock(Protocol):
    """Protocol for pluggable clocks used in tests."""

    def now(self) -> datetime:  # pragma: no cover - structural protocol
        """Return the current time as a timezone-aware datetime."""


class PromptRepository:
    """Filesystem-backed repository for generator prompts."""

    def __init__(self, base_path: Path) -> None:
        self._base_path = Path(base_path)

    def load(self, prompt_id: str) -> Mapping[str, Any]:
        path = self.path_for(prompt_id)
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def path_for(self, prompt_id: str) -> Path:
        """Return the filesystem path for a prompt identifier."""

        return self._resolve_prompt_path(prompt_id)

    def _resolve_prompt_path(self, prompt_id: str) -> Path:
        """Resolve a prompt identifier to a JSON file."""

        candidate = self._base_path / f"{prompt_id}.json"
        if candidate.exists():
            return candidate
        path = self._base_path / prompt_id
        if path.exists():
            return path
        raise FileNotFoundError(f"Prompt '{prompt_id}' not found under {self._base_path}")


@dataclass(frozen=True)
class GeneratorConfig:
    """Configuration for generator runs."""

    prompt_id: str
    prompt_parameters: Mapping[str, Any] = field(default_factory=dict)
    seed: int = 0


@dataclass(frozen=True)
class GeneratorProposal:
    """Structured generator output passed to the critic."""

    proposal_id: str
    prompt_id: str
    timestamp: str
    config_hash: str
    payload: Mapping[str, Any]
    provenance: Mapping[str, Any]


class Generator:
    """Generator agent that assembles proposals from prompts and config."""

    def __init__(
        self,
        prompt_repository: PromptRepository,
        log_sink: Optional[LogSink] = None,
        clock: Optional[Clock] = None,
    ) -> None:
        self._prompts = prompt_repository
        self._log = log_sink or NullLogSink()
        self._clock = clock or _UTCClock()

    def generate(self, config: GeneratorConfig) -> GeneratorProposal:
        prompt_content = self._prompts.load(config.prompt_id)
        timestamp = self._clock.now().isoformat()
        config_hash = _hash_config(config)
        proposal_id = _proposal_id(config.prompt_id, config.seed, config_hash)
        payload = _build_payload(prompt_content, config.prompt_parameters)
        provenance = {
            "prompt_id": config.prompt_id,
            "prompt_path": str(self._prompts.path_for(config.prompt_id)),
            "seed": config.seed,
            "parameters": dict(config.prompt_parameters),
        }
        proposal = GeneratorProposal(
            proposal_id=proposal_id,
            prompt_id=config.prompt_id,
            timestamp=timestamp,
            config_hash=config_hash,
            payload=payload,
            provenance=provenance,
        )
        self._log.write(
            {
                "event": "generator.proposal",
                "proposal": proposal.payload,
                "metadata": {
                    "proposal_id": proposal.proposal_id,
                    "timestamp": proposal.timestamp,
                    "config_hash": proposal.config_hash,
                    "provenance": proposal.provenance,
                },
            }
        )
        return proposal


def _hash_config(config: GeneratorConfig) -> str:
    payload = {
        "prompt_id": config.prompt_id,
        "prompt_parameters": dict(sorted(config.prompt_parameters.items())),
        "seed": config.seed,
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8"))
    return digest.hexdigest()


def _proposal_id(prompt_id: str, seed: int, config_hash: str) -> str:
    namespace = uuid.uuid5(uuid.NAMESPACE_URL, "synesthetic-labs/generator")
    return str(uuid.uuid5(namespace, f"{prompt_id}:{seed}:{config_hash}"))


def _build_payload(prompt_content: Mapping[str, Any], parameters: Mapping[str, Any]) -> Mapping[str, Any]:
    return {
        "prompt": dict(prompt_content),
        "parameters": dict(parameters),
    }


class _UTCClock:
    """Default timezone-aware clock."""

    def now(self) -> datetime:
        return datetime.now(timezone.utc)
