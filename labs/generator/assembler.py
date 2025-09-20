"""Asset assembler for Generator v0.3."""

from __future__ import annotations

import datetime as _dt
import uuid
from copy import deepcopy
from typing import Dict, Iterable, List, Optional, Set

from .control import ControlGenerator
from .haptic import HapticGenerator
from .meta import MetaGenerator
from .modulation import ModulationGenerator
from .rule_bundle import RuleBundleGenerator
from .shader import ShaderGenerator
from .tone import ToneGenerator


class AssetAssembler:
    """Compose component generators into a full Synesthetic asset."""

    def __init__(
        self,
        *,
        version: str = "v0.3",
        shader_generator: Optional[ShaderGenerator] = None,
        tone_generator: Optional[ToneGenerator] = None,
        haptic_generator: Optional[HapticGenerator] = None,
        control_generator: Optional[ControlGenerator] = None,
        modulation_generator: Optional[ModulationGenerator] = None,
        rule_bundle_generator: Optional[RuleBundleGenerator] = None,
        meta_generator: Optional[MetaGenerator] = None,
    ) -> None:
        self.version = version
        self._shader = shader_generator or ShaderGenerator(version=version)
        self._tone = tone_generator or ToneGenerator(version=version)
        self._haptic = haptic_generator or HapticGenerator(version=version)
        self._control = control_generator or ControlGenerator(version=version)
        self._modulation = modulation_generator or ModulationGenerator(version=version)
        self._rule_bundle = rule_bundle_generator or RuleBundleGenerator(version=version)
        self._meta = meta_generator or MetaGenerator(version=version)

    def generate(self, prompt: str, *, seed: Optional[int] = None) -> Dict[str, object]:
        """Return a fully wired Synesthetic asset for *prompt*."""

        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")

        timestamp = _dt.datetime.now(tz=_dt.timezone.utc).isoformat()

        shader = deepcopy(self._shader.generate(seed=seed))
        tone = deepcopy(self._tone.generate(seed=seed))
        haptic = deepcopy(self._haptic.generate(seed=seed))
        control_component = deepcopy(self._control.generate(seed=seed))
        modulation_component = deepcopy(self._modulation.generate(seed=seed))
        rule_bundle = deepcopy(self._rule_bundle.generate(seed=seed))
        meta = deepcopy(self._meta.generate(seed=seed))

        parameter_index = self._collect_parameters(shader, tone, haptic)

        mappings = self._prune_controls(control_component.get("mappings", []), parameter_index)
        modulators = self._prune_modulators(
            modulation_component.get("modulators", []), parameter_index
        )
        sanitized_rule_bundle = self._prune_rule_bundle(rule_bundle, parameter_index)

        control_component["mappings"] = mappings
        modulation_component["modulators"] = modulators

        asset_id = str(uuid.uuid4())
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
            "modulation": modulation_component,
            "rule_bundle": sanitized_rule_bundle,
            "meta": meta,
            "controls": mappings,
            "modulations": modulators,
            "parameter_index": sorted(parameter_index),
        }

        return asset

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

    @staticmethod
    def _prune_modulators(
        modulators: Iterable[Dict[str, object]], parameter_index: Set[str]
    ) -> List[Dict[str, object]]:
        sanitized: List[Dict[str, object]] = []
        for modulator in modulators:
            target = modulator.get("target")
            if target in parameter_index:
                sanitized.append(deepcopy(modulator))
        return sanitized

    @staticmethod
    def _prune_rule_bundle(
        rule_bundle: Dict[str, object], parameter_index: Set[str]
    ) -> Dict[str, object]:
        bundle = deepcopy(rule_bundle)
        rules = bundle.get("rules", [])
        sanitized_rules: List[Dict[str, object]] = []
        for rule in rules:  # type: ignore[assignment]
            effects = rule.get("effects", [])  # type: ignore[assignment]
            sanitized_effects: List[Dict[str, object]] = []
            for effect in effects:
                target = effect.get("target")
                if target is not None and target not in parameter_index:
                    continue
                sanitized_effects.append(deepcopy(effect))
            if sanitized_effects:
                rule_copy = deepcopy(rule)
                rule_copy["effects"] = sanitized_effects
                sanitized_rules.append(rule_copy)
        bundle["rules"] = sanitized_rules
        return bundle
