"""Asset assembler for Generator v0.1."""

from __future__ import annotations

import datetime as _dt
import hashlib
import uuid
from copy import deepcopy
from typing import Dict, Iterable, List, Optional, Set

from labs.experimental import ModulationGenerator, RuleBundleGenerator

from .control import ControlGenerator
from .haptic import HapticGenerator
from .meta import MetaGenerator
from .shader import ShaderGenerator
from .tone import ToneGenerator


class AssetAssembler:
    """Compose component generators into a full Synesthetic asset."""

    def __init__(
        self,
        *,
        version: str = "v0.2",
        shader_generator: Optional[ShaderGenerator] = None,
        tone_generator: Optional[ToneGenerator] = None,
        haptic_generator: Optional[HapticGenerator] = None,
        control_generator: Optional[ControlGenerator] = None,
        meta_generator: Optional[MetaGenerator] = None,
        modulation_generator: Optional[ModulationGenerator] = None,
        rule_bundle_generator: Optional[RuleBundleGenerator] = None,
    ) -> None:
        self.version = version
        self._shader = shader_generator or ShaderGenerator(version=version)
        self._tone = tone_generator or ToneGenerator(version=version)
        self._haptic = haptic_generator or HapticGenerator(version=version)
        self._control = control_generator or ControlGenerator(version=version)
        self._meta = meta_generator or MetaGenerator(version=version)
        self._modulation = modulation_generator or ModulationGenerator(version=version)
        self._rule_bundle = rule_bundle_generator or RuleBundleGenerator(version=version)

    def generate(self, prompt: str, *, seed: Optional[int] = None) -> Dict[str, object]:
        """Return a fully wired Synesthetic asset for *prompt*."""

        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")

        if seed is not None:
            asset_id, timestamp = self._deterministic_identifiers(prompt, seed)
        else:
            timestamp = _dt.datetime.now(tz=_dt.timezone.utc).isoformat()
            asset_id = str(uuid.uuid4())

        shader = deepcopy(self._shader.generate(seed=seed))
        tone = deepcopy(self._tone.generate(seed=seed))
        haptic = deepcopy(self._haptic.generate(seed=seed))
        control_component = deepcopy(self._control.generate(seed=seed))
        meta = deepcopy(self._meta.generate(seed=seed))
        modulation = deepcopy(self._modulation.generate(seed=seed))
        rule_bundle = deepcopy(self._rule_bundle.generate(seed=seed))

        parameter_index = self._collect_parameters(shader, tone, haptic)

        mappings = self._prune_controls(control_component.get("mappings", []), parameter_index)

        control_component["mappings"] = mappings

        asset: Dict[str, object] = {
            "id": asset_id,
            "prompt": prompt,
            "seed": seed,
            "timestamp": timestamp,
            "provenance": {
                "agent": "AssetAssembler",
                "version": self.version,
                "assembled_at": timestamp,
                "seed": seed,
            },
            "shader": shader,
            "tone": tone,
            "haptic": haptic,
            "control": control_component,
            "meta": meta,
            "modulation": modulation,
            "rule_bundle": rule_bundle,
            "controls": mappings,
            "parameter_index": sorted(parameter_index),
        }

        return asset

    def _deterministic_identifiers(self, prompt: str, seed: int) -> tuple[str, str]:
        digest = hashlib.sha1(f"{prompt}|{seed}|{self.version}".encode("utf-8")).hexdigest()
        uuid_hex = digest[:32]
        asset_id = str(uuid.UUID(hex=uuid_hex))

        base = _dt.datetime(2024, 1, 1, tzinfo=_dt.timezone.utc)
        offset_seconds = int(digest[32:], 16) % (365 * 24 * 60 * 60)
        timestamp = (base + _dt.timedelta(seconds=offset_seconds)).isoformat()
        return asset_id, timestamp

    @staticmethod
    def _collect_parameters(*sections: Dict[str, object]) -> Set[str]:
        parameters: Set[str] = set()
        for section in sections:
            for entry in section.get("input_parameters", []):  # type: ignore[assignment]
                parameter = entry.get("parameter")  # type: ignore[assignment]
                if parameter:
                    parameters.add(parameter)
        return parameters

    @staticmethod
    def _prune_controls(
        mappings: Iterable[Dict[str, object]], parameter_index: Set[str]
    ) -> List[Dict[str, object]]:
        sanitized: List[Dict[str, object]] = []
        for mapping in mappings:
            parameter = mapping.get("parameter")
            if parameter in parameter_index:
                sanitized.append(deepcopy(mapping))
        return sanitized
