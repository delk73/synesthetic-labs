"""Generator agent responsible for assembling proposals for critic review."""
from __future__ import annotations

import hashlib
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from labs.logging import log_jsonl

PromptData = Dict[str, Any]
Proposal = Dict[str, Any]


def _default_clock() -> datetime:
    """Return the current UTC time."""
    return datetime.now(timezone.utc)


def _default_id_factory(seed: str) -> str:
    """Derive a deterministic identifier from *seed*."""
    return uuid.uuid5(uuid.NAMESPACE_URL, seed).hex


@dataclass
class GeneratorAgent:
    """Load prompts and produce structured asset proposals."""

    prompts_dir: Path | str = Path("meta/prompts")
    output_path: Path | str = Path("meta/output/generator.log.jsonl")
    clock: Callable[[], datetime] = field(default_factory=_default_clock)
    id_factory: Callable[[str], str] = field(default=_default_id_factory)

    def __post_init__(self) -> None:
        self.prompts_dir = Path(self.prompts_dir)
        self.output_path = Path(self.output_path)
        self.logger = logging.getLogger(self.__class__.__name__)

    # Public API ---------------------------------------------------------
    def propose(
        self,
        prompt_id: str,
        *,
        config: Optional[Dict[str, Any]] = None,
        dataset_context: Optional[Dict[str, Any]] = None,
    ) -> Proposal:
        """Return a structured proposal for *prompt_id*.

        Parameters
        ----------
        prompt_id:
            Identifier of the prompt stored under ``self.prompts_dir``.
        config:
            Optional configuration dictionary that influences proposal shaping.
        dataset_context:
            Optional context describing datasets used while assembling the proposal.
        """

        prompt = self._load_prompt(prompt_id)
        timestamp = self.clock().replace(microsecond=0, tzinfo=timezone.utc)
        config_payload = config or {}
        dataset_payload = dataset_context or {}
        config_hash = self._hash_config(config_payload)
        seed = "|".join([prompt_id, timestamp.isoformat(), config_hash])
        proposal_id = self.id_factory(seed)

        asset = self._shape_asset(prompt, config_payload, dataset_payload)
        provenance = {
            "prompt_id": prompt_id,
            "prompt_path": str(self._resolve_prompt_path(prompt_id)),
            "generated_at": timestamp.isoformat(),
            "config_hash": config_hash,
        }

        proposal: Proposal = {
            "proposal_id": proposal_id,
            "prompt_id": prompt_id,
            "prompt": prompt,
            "asset": asset,
            "config": config_payload,
            "config_hash": config_hash,
            "dataset_context": dataset_payload,
            "generated_at": timestamp.isoformat(),
            "provenance": provenance,
        }

        log_jsonl(self.output_path, {"event": "generator.propose", "proposal": proposal})
        self.logger.debug("Generated proposal %s for prompt %s", proposal_id, prompt_id)
        return proposal

    # Internal helpers ---------------------------------------------------
    def _load_prompt(self, prompt_id: str) -> PromptData:
        path = self._resolve_prompt_path(prompt_id)
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _resolve_prompt_path(self, prompt_id: str) -> Path:
        candidate = Path(prompt_id)
        if candidate.suffix:
            path = self.prompts_dir / candidate
        else:
            path = self.prompts_dir / f"{prompt_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Prompt '{prompt_id}' not found under {self.prompts_dir}")
        return path

    def _hash_config(self, config: Dict[str, Any]) -> str:
        payload = json.dumps(config, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _shape_asset(
        self,
        prompt: PromptData,
        config: Dict[str, Any],
        dataset_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Project prompt + config into a proposal asset structure."""
        return {
            "type": prompt.get("task", "generic-asset"),
            "description": prompt.get("objective", ""),
            "constraints": prompt.get("constraints", {}),
            "config": config,
            "dataset_context": dataset_context,
        }
