"""Asset assembler for Generator v0.3.x flattened Synesthetic assets."""

from __future__ import annotations

import datetime as _dt
import hashlib
import uuid
from copy import deepcopy
from typing import Dict, Iterable, List, Optional, Sequence, Set

from labs.experimental import ModulationGenerator, RuleBundleGenerator

from .control import ControlGenerator
from .haptic import HapticGenerator
from .meta import MetaGenerator
from .shader import ShaderGenerator
from .tone import ToneGenerator


class AssetAssembler:
    """Compose component generators into a full Synesthetic asset."""

    DEFAULT_SCHEMA_VERSION = "0.7.3"
    SCHEMA_URL_TEMPLATE = "https://schemas.synesthetic.dev/{version}/synesthetic-asset.schema.json"

    @classmethod
    def schema_url(cls, schema_version: str) -> str:
        """Return the hosted schema URL for *schema_version*."""

        version = (schema_version or cls.DEFAULT_SCHEMA_VERSION).strip()
        return cls.SCHEMA_URL_TEMPLATE.format(version=version)


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

    def generate(
        self,
        prompt: str,
        *,
        seed: Optional[int] = None,
        schema_version: str = DEFAULT_SCHEMA_VERSION,
    ) -> Dict[str, object]:
        """Return a fully wired Synesthetic asset for *prompt*."""

        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")

        if seed is not None:
            asset_id, timestamp = self._deterministic_identifiers(prompt, seed)
        else:
            timestamp = _dt.datetime.now(tz=_dt.timezone.utc).isoformat()
            asset_id = str(uuid.uuid4())

        resolved_version = (schema_version or self.DEFAULT_SCHEMA_VERSION).strip()
        legacy_payload = resolved_version.startswith("0.7.3")
        schema_url = self.schema_url(resolved_version)

        shader = deepcopy(self._shader.generate(seed=seed))
        tone = deepcopy(self._tone.generate(seed=seed))
        haptic = deepcopy(self._haptic.generate(seed=seed))
        control_component = deepcopy(self._control.generate(seed=seed))
        meta = deepcopy(self._meta.generate(seed=seed))
        modulation = deepcopy(self._modulation.generate(seed=seed))
        rule_bundle = deepcopy(self._rule_bundle.generate(seed=seed))

        parameter_index = self._collect_parameters(shader, tone, haptic)

        pruned_mappings = self._prune_controls(
            control_component.get("mappings", []), parameter_index
        )

        shader_block = self._build_shader(shader)
        tone_block = self._build_tone(tone)
        haptic_block = self._build_haptic(haptic)
        control_block = self._build_control(control_component, pruned_mappings)
        modulations_block = self._build_modulations(modulation)
        rule_bundle_block = self._build_rule_bundle(rule_bundle)
        meta_info_block = self._build_meta_info(
            meta,
            timestamp,
            seed,
            asset_id,
            include_provenance=legacy_payload,
        )

        provenance_block = self._build_asset_provenance(
            timestamp=timestamp,
            seed=seed,
            asset_id=asset_id,
            trace_id=asset_id,
            schema_version=resolved_version,
        )

        asset: Dict[str, object] = {
            "$schema": schema_url,
            "seed": seed,
            "shader": shader_block,
            "tone": tone_block,
            "haptic": haptic_block,
            "control": control_block,
            "modulations": modulations_block,
            "rule_bundle": rule_bundle_block,
            "meta_info": meta_info_block,
        }

        if legacy_payload:
            asset["name"] = prompt
            meta_info_block.setdefault("title", prompt)
            meta_info_block.setdefault(
                "provenance",
                self._build_meta_provenance(
                    timestamp=timestamp,
                    seed=seed,
                    trace_id=asset_id,
                ),
            )
        else:
            asset.update(
                {
                    "asset_id": asset_id,
                    "prompt": prompt,
                    "timestamp": timestamp,
                    "parameter_index": sorted(parameter_index),
                    "provenance": provenance_block,
                }
            )
            meta_info_block.setdefault("title", prompt)

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

    def _build_shader(self, payload: Dict[str, object]) -> Dict[str, object]:
        shader = deepcopy(payload)
        shader.pop("component", None)
        version = shader.pop("version", None)
        if version:
            shader.setdefault("meta_info", {})["version"] = version
        return shader

    def _build_tone(self, payload: Dict[str, object]) -> Dict[str, object]:
        tone = deepcopy(payload)
        tone.pop("component", None)
        version = tone.pop("version", None)
        if version:
            tone.setdefault("meta_info", {})["version"] = version
        return tone

    def _build_haptic(self, payload: Dict[str, object]) -> Dict[str, object]:
        haptic = deepcopy(payload)
        haptic.pop("component", None)
        version = haptic.pop("version", None)
        if version:
            haptic.setdefault("meta_info", {})["version"] = version
        return haptic

    def _build_control(
        self,
        payload: Dict[str, object],
        mappings: Sequence[Dict[str, object]],
    ) -> Dict[str, object]:
        control: Dict[str, object] = {
            "name": "Pointer Input Controls",
            "control_parameters": self._build_control_parameters(mappings),
        }
        version = payload.get("version")
        if version:
            control.setdefault("meta_info", {})["version"] = version
        description = payload.get("description")
        if description:
            control["description"] = description
        return control

    def _build_control_parameters(
        self, mappings: Sequence[Dict[str, object]]
    ) -> List[Dict[str, object]]:
        parameters: List[Dict[str, object]] = []
        for mapping in mappings:
            parameter = mapping.get("parameter")
            if not isinstance(parameter, str):
                continue
            control_input = mapping.get("input")
            device = None
            control_axis = None
            if isinstance(control_input, dict):
                device = control_input.get("device")
                control_axis = control_input.get("control")
            combo_entry: Dict[str, Optional[str]] = {
                "device": device,
                "control": control_axis,
            }
            entry: Dict[str, object] = {
                "id": mapping.get("id") or parameter.replace(".", "_"),
                "parameter": parameter,
                "label": self._derive_control_label(device, control_axis, parameter),
                "unit": self._derive_control_unit(parameter),
                "sensitivity": mapping.get("sensitivity", 1.0),
                "combo": [combo_entry],
                "mode": mapping.get("mode", "absolute"),
                "curve": mapping.get("curve", "linear"),
            }
            if "invert" in mapping:
                entry["invert"] = mapping.get("invert")
            range_block = mapping.get("range")
            if isinstance(range_block, dict):
                entry["range"] = deepcopy(range_block)
            parameters.append(entry)
        return parameters

    @staticmethod
    def _derive_control_label(
        device: Optional[str], control_axis: Optional[str], parameter: str
    ) -> str:
        if device and control_axis:
            return f"{device}.{control_axis}"
        return parameter

    @staticmethod
    def _derive_control_unit(parameter: str) -> str:
        if parameter.startswith("shader."):
            return "normalized"
        if parameter.startswith("tone."):
            return "audio"
        if parameter.startswith("haptic."):
            return "haptic"
        return "generic"

    def _build_modulations(self, payload: Dict[str, object]) -> List[Dict[str, object]]:
        modulators = payload.get("modulators")
        if isinstance(modulators, list):
            return deepcopy(modulators)
        return []

    def _build_rule_bundle(self, payload: Dict[str, object]) -> Dict[str, object]:
        rules = payload.get("rules")
        if not isinstance(rules, list):
            rules = []
        bundle: Dict[str, object] = {
            "name": payload.get("name", "Baseline rule bundle"),
            "description": payload.get(
                "description",
                "Canonical grid-driven interactions for the baseline asset.",
            ),
            "rules": deepcopy(rules),
            "meta_info": {
                "version": payload.get("version", self.version),
            },
        }
        return bundle

    def _build_meta_info(
        self,
        payload: Dict[str, object],
        timestamp: str,
        seed: Optional[int],
        asset_id: str,
        *,
        include_provenance: bool,
    ) -> Dict[str, object]:
        meta = deepcopy(payload)
        meta.pop("component", None)
        meta.pop("version", None)
        meta.setdefault("title", "Synesthetic Asset")
        meta.setdefault(
            "description",
            "Synesthetic asset synthesized by the AssetAssembler baseline.",
        )
        meta.setdefault("category", "multimodal")
        meta.setdefault("complexity", "baseline")
        tags = meta.get("tags")
        if not isinstance(tags, list):
            meta["tags"] = ["baseline", "assembler"]
        provenance = meta.get("provenance")
        if not isinstance(provenance, dict):
            meta["provenance"] = self._build_meta_provenance(
                timestamp=timestamp, seed=seed, trace_id=asset_id
            )
        return meta

    def _build_meta_provenance(
        self,
        *,
        timestamp: str,
        seed: Optional[int],
        trace_id: str,
    ) -> Dict[str, object]:
        return {
            "engine": "deterministic",
            "endpoint": "internal",
            "model": "AssetAssembler",
            "parameters": {
                "seed": seed,
                "version": self.version,
            },
            "trace_id": trace_id,
            "mode": "local",
            "timestamp": timestamp,
            "response_hash": None,
        }

    def _build_asset_provenance(
        self,
        *,
        timestamp: str,
        seed: Optional[int],
        asset_id: str,
        trace_id: str,
        schema_version: str,
    ) -> Dict[str, object]:
        return {
            "agent": "AssetAssembler",
            "version": self.version,
            "assembled_at": timestamp,
            "seed": seed,
            "generator": {
                "trace_id": trace_id,
                "mode": "local",
                "engine": "deterministic",
            },
            "asset_id": asset_id,
            "schema_version": schema_version,
        }


# Backwards compatibility: retain default schema URL attribute used by older callers.
AssetAssembler.SCHEMA_URL = AssetAssembler.schema_url(AssetAssembler.DEFAULT_SCHEMA_VERSION)
