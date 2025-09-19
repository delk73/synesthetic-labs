"""Unit tests for individual component generators."""

from __future__ import annotations

import os
from typing import Any, Dict, Iterable, Set

import pytest

from labs.agents.critic import MCPUnavailableError
from labs.cli import SocketMCPValidator
from labs.generator import (
    ControlGenerator,
    HapticGenerator,
    MetaGenerator,
    ModulationGenerator,
    RuleBundleGenerator,
    ShaderGenerator,
    ToneGenerator,
)


@pytest.fixture()
def shader_section() -> Dict[str, Any]:
    return ShaderGenerator().generate()


@pytest.fixture()
def tone_section() -> Dict[str, Any]:
    return ToneGenerator().generate()


@pytest.fixture()
def haptic_section() -> Dict[str, Any]:
    return HapticGenerator().generate()


@pytest.fixture()
def control_section() -> Dict[str, Any]:
    return ControlGenerator().generate()


@pytest.fixture()
def modulation_section() -> Dict[str, Any]:
    return ModulationGenerator().generate()


@pytest.fixture()
def rule_bundle_section() -> Dict[str, Any]:
    return RuleBundleGenerator().generate()


@pytest.fixture()
def meta_section() -> Dict[str, Any]:
    return MetaGenerator().generate()


def _parameter_names(sections: Iterable[Dict[str, Any]]) -> Set[str]:
    names: Set[str] = set()
    for section in sections:
        for entry in section.get("input_parameters", []):
            parameter = entry.get("parameter")
            if parameter:
                names.add(parameter)
    return names


def _build_full_asset(sections: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    shader = sections["shader"]
    tone = sections["tone"]
    haptic = sections["haptic"]
    control = sections["control"]
    modulation = sections["modulation"]
    rule_bundle = sections["rule_bundle"]
    meta = sections["meta"]

    return {
        "shader": shader,
        "tone": tone,
        "haptic": haptic,
        "controls": control.get("mappings", []),
        "modulations": modulation.get("modulators", []),
        "rule_bundle": rule_bundle,
        "meta": meta,
    }


def _maybe_validate_with_mcp(asset: Dict[str, Any]) -> Dict[str, Any]:
    host = os.getenv("MCP_HOST")
    port_value = os.getenv("MCP_PORT")
    schemas_dir = os.getenv("SYN_SCHEMAS_DIR")

    if not host or not port_value or not schemas_dir:
        pytest.skip("MCP validation requires MCP_HOST, MCP_PORT, and SYN_SCHEMAS_DIR")

    try:
        port = int(port_value)
    except (TypeError, ValueError):
        pytest.skip("MCP_PORT is not a valid integer")

    validator = SocketMCPValidator(host, port)
    try:
        return validator.validate(asset)
    except MCPUnavailableError as exc:
        pytest.skip(f"MCP unavailable: {exc}")
    except OSError as exc:
        pytest.skip(f"MCP unavailable: {exc}")


def test_shader_generator_exposes_parameters(shader_section: Dict[str, Any]) -> None:
    assert shader_section["name"] == "CircleSDF"
    parameters = {entry["parameter"] for entry in shader_section["input_parameters"]}
    assert parameters == {"shader.u_px", "shader.u_py", "shader.u_r"}


def test_tone_generator_parameters(tone_section: Dict[str, Any]) -> None:
    assert tone_section["engine"] == "Tone.Synth"
    parameters = {entry["parameter"] for entry in tone_section["input_parameters"]}
    assert {"tone.volume", "tone.detune", "tone.portamento"}.issubset(parameters)


def test_haptic_generator_parameters(haptic_section: Dict[str, Any]) -> None:
    assert haptic_section["device"] == "generic"
    parameters = {entry["parameter"] for entry in haptic_section["input_parameters"]}
    assert parameters == {"haptic.intensity", "haptic.frequency"}


def test_control_mappings_reference_known_parameters(
    shader_section: Dict[str, Any],
    tone_section: Dict[str, Any],
    haptic_section: Dict[str, Any],
    control_section: Dict[str, Any],
) -> None:
    known_parameters = _parameter_names([shader_section, tone_section, haptic_section])
    assert control_section["mappings"], "control mappings should not be empty"
    for mapping in control_section["mappings"]:
        assert mapping["parameter"] in known_parameters


def test_modulations_reference_known_parameters(
    shader_section: Dict[str, Any],
    tone_section: Dict[str, Any],
    haptic_section: Dict[str, Any],
    modulation_section: Dict[str, Any],
) -> None:
    known_parameters = _parameter_names([shader_section, tone_section, haptic_section])
    assert modulation_section["modulators"], "modulation list should not be empty"
    for modulator in modulation_section["modulators"]:
        assert modulator["target"] in known_parameters


def test_rule_bundle_effect_targets_are_known(
    shader_section: Dict[str, Any],
    tone_section: Dict[str, Any],
    haptic_section: Dict[str, Any],
    rule_bundle_section: Dict[str, Any],
) -> None:
    known_parameters = _parameter_names([shader_section, tone_section, haptic_section])
    rules = rule_bundle_section["rules"]
    assert rules, "rule bundle should define at least one rule"
    for rule in rules:
        effects = rule.get("effects", [])
        assert effects, "each rule should define effects"
        for effect in effects:
            target = effect.get("target")
            if target is not None:
                assert target in known_parameters


def test_meta_generator_fields(meta_section: Dict[str, Any]) -> None:
    for key in ("title", "description", "category", "complexity", "tags"):
        assert key in meta_section
    assert meta_section["category"] == "multimodal"


def test_component_bundle_validates_with_mcp(
    shader_section: Dict[str, Any],
    tone_section: Dict[str, Any],
    haptic_section: Dict[str, Any],
    control_section: Dict[str, Any],
    modulation_section: Dict[str, Any],
    rule_bundle_section: Dict[str, Any],
    meta_section: Dict[str, Any],
) -> None:
    asset = _build_full_asset(
        {
            "shader": shader_section,
            "tone": tone_section,
            "haptic": haptic_section,
            "control": control_section,
            "modulation": modulation_section,
            "rule_bundle": rule_bundle_section,
            "meta": meta_section,
        }
    )

    response = _maybe_validate_with_mcp(asset)
    assert isinstance(response, dict)
