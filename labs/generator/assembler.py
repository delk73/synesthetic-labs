"""Asset assembler for Generator v0.3.x flattened Synesthetic assets."""

from __future__ import annotations

import datetime as _dt
import hashlib
import os
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
    SCHEMA_URL = SCHEMA_URL_TEMPLATE.format(version=DEFAULT_SCHEMA_VERSION)

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
        schema_version: str = DEFAULT_SCHEMA_VERSION,
    ) -> None:
        self.version = version
        self._shader = shader_generator or ShaderGenerator(version=version)
        self._tone = tone_generator or ToneGenerator(version=version)
        self._haptic = haptic_generator or HapticGenerator(version=version)
        self._control = control_generator or ControlGenerator(version=version)
        self._meta = meta_generator or MetaGenerator(version=version)
        self._modulation = modulation_generator or ModulationGenerator(version=version)
        self._rule_bundle = rule_bundle_generator or RuleBundleGenerator(version=version)
        self.schema_version = schema_version or self.DEFAULT_SCHEMA_VERSION

    @classmethod
    def schema_url(cls, schema_version: str) -> str:
        version = (schema_version or cls.DEFAULT_SCHEMA_VERSION).strip()
        return cls.SCHEMA_URL_TEMPLATE.format(version=version)

    @staticmethod
    def default_shader() -> Dict[str, object]:
        return {"type": "fragment", "code": "// default shader"}

    @staticmethod
    def default_tone() -> Dict[str, object]:
        return {"type": "sine", "frequency": 440}

    @staticmethod
    def default_haptic() -> Dict[str, object]:
        return {"pattern": "pulse", "duration_ms": 120}

    @staticmethod
    def default_control() -> Dict[str, object]:
        return {"sensitivity": 1.0, "range": [0, 1]}

    @staticmethod
    def fill_defaults(asset: Dict[str, object]) -> Dict[str, object]:
        if not isinstance(asset, dict):
            return asset

        fillers = {
            "shader": AssetAssembler.default_shader,
            "tone": AssetAssembler.default_tone,
            "haptic": AssetAssembler.default_haptic,
            "control": AssetAssembler.default_control,
        }

        for section, factory in fillers.items():
            value = asset.get(section)
            if not isinstance(value, dict) or not value:
                asset[section] = factory()
        return asset

    def generate(
        self,
        prompt: str,
        *,
        seed: Optional[int] = None,
        schema_version: Optional[str] = None,
    ) -> Dict[str, object]:
        """Return a fully wired Synesthetic asset for *prompt*."""

        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")

        resolved_schema_version = (schema_version or self.schema_version) or self.DEFAULT_SCHEMA_VERSION

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

        pruned_mappings = self._prune_controls(
            control_component.get("mappings", []), parameter_index
        )

        shader_block = self._build_shader(shader)
        tone_block = self._build_tone(tone)
        haptic_block = self._build_haptic(haptic)
        control_block = self._build_control(control_component, pruned_mappings)
        modulations_block = self._build_modulations(modulation)
        rule_bundle_block = self._build_rule_bundle(rule_bundle)
        meta_info_block = self._build_meta_info(meta, timestamp, seed, asset_id)

        provenance_block = self._build_asset_provenance(
            engine="deterministic",
            schema_version=resolved_schema_version,
            assembler_version=self.version,
            trace_id=asset_id,
            input_parameters={"prompt": prompt, "seed": seed},
        )

        schema_url = self.schema_url(resolved_schema_version)

        meta_info_block.setdefault("provenance", self._build_meta_provenance(
            timestamp=timestamp,
            seed=seed,
            trace_id=asset_id,
        ))

        base_sections: Dict[str, object] = {
            "shader": shader_block,
            "tone": tone_block,
            "haptic": haptic_block,
            "control": control_block,
            "modulations": modulations_block,
            "rule_bundle": rule_bundle_block,
            "meta_info": meta_info_block,
        }

        if self._is_legacy_schema(resolved_schema_version):
            return self._build_legacy_asset(
                schema_url=schema_url,
                prompt=prompt,
                asset_id=asset_id,
                timestamp=timestamp,
                base_sections=base_sections,
                rule_bundle_version=self.version,
            )

        return self._build_enriched_asset(
            schema_url=schema_url,
            prompt=prompt,
            asset_id=asset_id,
            timestamp=timestamp,
            parameter_index=parameter_index,
            provenance_block=provenance_block,
            base_sections=base_sections,
            seed=seed,
            rule_bundle_version=self.version,
        )

    @staticmethod
    def _is_legacy_schema(schema_version: Optional[str]) -> bool:
        if not schema_version:
            return False
        return schema_version.strip().startswith("0.7.3")

    @staticmethod
    def _build_legacy_asset(
        *,
        schema_url: str,
        prompt: str,
        asset_id: str,
        timestamp: str,
        base_sections: Dict[str, object],
        rule_bundle_version: Optional[str] = None,
    ) -> Dict[str, object]:
        sections = deepcopy(base_sections)

        if not isinstance(sections.get("shader"), dict):
            sections["shader"] = {}
        if not isinstance(sections.get("tone"), dict):
            sections["tone"] = {}
        if not isinstance(sections.get("haptic"), dict):
            sections["haptic"] = {}
        if not isinstance(sections.get("control"), dict):
            sections["control"] = {"control_parameters": []}

        modulations = sections.get("modulations")
        if not isinstance(modulations, list):
            sections["modulations"] = []

        rule_bundle = sections.get("rule_bundle")
        if not isinstance(rule_bundle, dict):
            rule_bundle = {"rules": [], "meta_info": {}}
            sections["rule_bundle"] = rule_bundle
        else:
            sections["rule_bundle"] = deepcopy(rule_bundle)
            rule_bundle = sections["rule_bundle"]

        AssetAssembler._ensure_rule_bundle_version(rule_bundle, rule_bundle_version)

        meta_info = sections.get("meta_info")
        if not isinstance(meta_info, dict):
            meta_info = {}
            sections["meta_info"] = meta_info

        AssetAssembler._ensure_meta_defaults(meta_info, prompt)
        AssetAssembler.fill_defaults(sections)

        legacy_asset: Dict[str, object] = {
            "$schema": schema_url,
            "asset_id": asset_id,
            "prompt": prompt,
            "timestamp": timestamp,
            "name": meta_info.get("title") or prompt,
        }
        legacy_asset.update(sections)
        return AssetAssembler.fill_defaults(legacy_asset)

    @staticmethod
    def _build_enriched_asset(
        *,
        schema_url: str,
        prompt: str,
        asset_id: str,
        timestamp: str,
        parameter_index: Sequence[str],
        provenance_block: Dict[str, object],
        base_sections: Dict[str, object],
        seed: Optional[int],
        rule_bundle_version: Optional[str] = None,
    ) -> Dict[str, object]:
        sections = deepcopy(base_sections)

        if not isinstance(sections.get("shader"), dict):
            sections["shader"] = {}
        if not isinstance(sections.get("tone"), dict):
            sections["tone"] = {}
        if not isinstance(sections.get("haptic"), dict):
            sections["haptic"] = {}

        control_block = sections.get("control")
        if not isinstance(control_block, dict):
            control_block = {"control_parameters": []}
            sections["control"] = control_block
        else:
            sections["control"] = deepcopy(control_block)

        if not isinstance(sections.get("modulations"), list):
            sections["modulations"] = []

        rule_bundle = sections.get("rule_bundle")
        if not isinstance(rule_bundle, dict):
            rule_bundle = {"rules": [], "meta_info": {}}
            sections["rule_bundle"] = rule_bundle
        else:
            sections["rule_bundle"] = deepcopy(rule_bundle)
            rule_bundle = sections["rule_bundle"]

        AssetAssembler._ensure_rule_bundle_version(rule_bundle, rule_bundle_version)

        meta_info = sections.get("meta_info")
        if not isinstance(meta_info, dict):
            meta_info = {}
            sections["meta_info"] = meta_info

        AssetAssembler._ensure_meta_defaults(meta_info, prompt)

        normalized_provenance = deepcopy(provenance_block) if isinstance(provenance_block, dict) else {}

        unique_parameters = sorted({param for param in parameter_index if isinstance(param, str)})

        enriched_asset: Dict[str, object] = {
            "$schema": schema_url,
            "asset_id": asset_id,
            "prompt": prompt,
            "seed": seed,
            "timestamp": timestamp,
            "parameter_index": unique_parameters,
            "provenance": normalized_provenance,
        }
        enriched_asset.update(sections)
        return enriched_asset

    @staticmethod
    def _ensure_rule_bundle_version(rule_bundle: Dict[str, object], fallback_version: Optional[str]) -> None:
        if not isinstance(rule_bundle, dict):
            return

        rules = rule_bundle.get("rules")
        if not isinstance(rules, list):
            rule_bundle["rules"] = []

        meta_info = rule_bundle.setdefault("meta_info", {})
        if not isinstance(meta_info, dict):
            meta_info = {}
            rule_bundle["meta_info"] = meta_info

        if fallback_version and not meta_info.get("version"):
            meta_info["version"] = fallback_version
        else:
            meta_info.setdefault("version", fallback_version)

    @staticmethod
    def _ensure_meta_defaults(meta_info: Dict[str, object], prompt: str) -> None:
        meta_info.setdefault("title", prompt)
        meta_info.setdefault(
            "description",
            "Synesthetic asset synthesized by the AssetAssembler baseline.",
        )
        meta_info.setdefault("category", "multimodal")
        meta_info.setdefault("complexity", "baseline")

        tags = meta_info.get("tags")
        if not isinstance(tags, list) or not tags:
            meta_info["tags"] = ["baseline", "assembler"]

        provenance = meta_info.get("provenance")
        if not isinstance(provenance, dict):
            meta_info["provenance"] = {}

    @staticmethod
    def _normalize_0_7_3(asset: Dict[str, object], prompt: str, assembler_version: str) -> Dict[str, object]:
        """Produce a schema 0.7.3–compliant asset (strip all enriched 0.7.4+ fields)."""
        schema_url = str(
            asset.get("$schema")
            or AssetAssembler.schema_url(AssetAssembler.DEFAULT_SCHEMA_VERSION)
        )

        normalized: Dict[str, object] = {
            "$schema": schema_url,
            "name": asset.get("meta_info", {}).get("title", prompt),
            "shader": {
                k: v for k, v in asset.get("shader", {}).items()
                if k in ("name", "description", "language", "sources", "uniforms", "meta_info")
            },
            "tone": {
                k: v for k, v in asset.get("tone", {}).items()
                if k in ("name", "description", "engine", "settings", "meta_info")
            },
            "haptic": {
                k: v for k, v in asset.get("haptic", {}).items()
                if k in ("device", "description", "input_parameters", "meta_info")
            },
            "control": asset.get("control", {}),
            "modulations": [],  # forbidden in 0.7.3
            "rule_bundle": {
                "name": asset.get("rule_bundle", {}).get("name", "default"),
                "rules": [],
                "meta_info": {"version": assembler_version},
            },
            "meta_info": {
                "provenance": asset.get("meta_info", {}).get("provenance", {})
            },
        }

        AssetAssembler.fill_defaults(normalized)

        provenance = normalized.get("meta_info", {}).get("provenance")
        if isinstance(provenance, dict):
            allowed_keys = {"engine", "trace_id", "timestamp"}
            normalized.setdefault("meta_info", {})["provenance"] = {
                key: value for key, value in provenance.items() if key in allowed_keys
            }

        return normalized



    @staticmethod
    def _normalize_0_7_4(
        asset: Dict[str, object],
        prompt: str,
        asset_id: str,
        timestamp: str,
        parameter_index: Sequence[str],
        provenance_block: Dict[str, object],
        rule_bundle_version: Optional[str] = None,
    ) -> Dict[str, object]:
        base_sections: Dict[str, object] = {
            "shader": deepcopy(asset.get("shader", {})),
            "tone": deepcopy(asset.get("tone", {})),
            "haptic": deepcopy(asset.get("haptic", {})),
            "control": deepcopy(asset.get("control", {})),
            "modulations": deepcopy(asset.get("modulations", [])),
            "rule_bundle": deepcopy(asset.get("rule_bundle", {})),
            "meta_info": deepcopy(asset.get("meta_info", {})),
        }

        schema_url = str(
            asset.get("$schema")
            or AssetAssembler.schema_url(AssetAssembler.DEFAULT_SCHEMA_VERSION)
        )

        effective_rule_bundle_version = rule_bundle_version
        rule_bundle = base_sections.get("rule_bundle")
        if effective_rule_bundle_version is None and isinstance(rule_bundle, dict):
            meta_info = rule_bundle.get("meta_info")
            if isinstance(meta_info, dict):
                version = meta_info.get("version")
                if isinstance(version, str):
                    effective_rule_bundle_version = version

        return AssetAssembler._build_enriched_asset(
            schema_url=schema_url,
            prompt=prompt,
            asset_id=asset_id,
            timestamp=timestamp,
            parameter_index=parameter_index,
            provenance_block=provenance_block,
            base_sections=base_sections,
            seed=asset.get("seed"),
            rule_bundle_version=effective_rule_bundle_version,
        )

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

    @staticmethod
    def _version_tuple(value: str) -> Optional[Sequence[int]]:
        try:
            return tuple(int(part) for part in str(value).split("."))
        except ValueError:
            return None

    @classmethod
    def _schema_gte(cls, version: str, target: str) -> bool:
        lhs = cls._version_tuple(version)
        rhs = cls._version_tuple(target)
        if lhs is not None and rhs is not None:
            return lhs >= rhs
        return str(version) >= str(target)

    @staticmethod
    def _build_asset_provenance(
        engine: str,
        *,
        schema_version: str = "0.7.3",
        assembler_version: str = "v0.2",
        trace_id: Optional[str] = None,
        input_parameters: Optional[Dict[str, object]] = None,
    ) -> Dict[str, object]:
        resolved_trace_id = str(trace_id) if trace_id else str(uuid.uuid4())
        assembled_at = _dt.datetime.utcnow().isoformat() + "Z"
        provenance: Dict[str, object] = {
            "agent": "AssetAssembler",
            "version": assembler_version,
            "engine": engine,
            "trace_id": resolved_trace_id,
            "timestamp": assembled_at,
            "assembled_at": assembled_at,
            "generator": {
                "class": "AssetAssembler",
                "engine": engine,
                "trace_id": resolved_trace_id,
                "mode": "local" if engine == "deterministic" else "external",
                "version": assembler_version,
            },
        }

        if input_parameters:
            provenance["generator"]["input_parameters"] = dict(input_parameters)
            if "seed" in input_parameters and input_parameters["seed"] is not None:
                provenance["seed"] = input_parameters["seed"]

        if AssetAssembler._schema_gte(schema_version, "0.7.4"):
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT") or os.getenv("GEMINI_ENDPOINT")
            deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT") or os.getenv("GEMINI_MODEL")
            api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
            if endpoint:
                provenance["generator"]["endpoint"] = endpoint
            if deployment:
                provenance["generator"]["deployment"] = deployment
            if api_version:
                provenance["generator"]["api_version"] = api_version

        return provenance
