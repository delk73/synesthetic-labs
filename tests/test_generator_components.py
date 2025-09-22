"""Unit tests for individual component generators."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Set

import pytest

from labs.generator import (
    ControlGenerator,
    HapticGenerator,
    MetaGenerator,
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



def test_meta_generator_fields(meta_section: Dict[str, Any]) -> None:
    for key in ("title", "description", "category", "complexity", "tags"):
        assert key in meta_section
    assert meta_section["category"] == "multimodal"
