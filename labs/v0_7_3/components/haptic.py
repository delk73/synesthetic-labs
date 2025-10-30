"""Haptic component builder for schema version 0.7.3."""

from __future__ import annotations

from typing import Any, Dict, List

from labs.v0_7_3.prompt_parser import PromptSemantics

from .common import (
    amplitude_from_intensity,
    append_tags,
    duration_from_semantics,
    ensure_semantics,
    sanitize_identifier,
)

_DEVICE_KEYWORDS = {
    "glove": "glove",
    "vest": "vest",
    "chair": "seat",
    "belt": "waist",
}


def build_haptic(
    prompt: str,
    subschema: Dict[str, Any],
    *,
    semantics: PromptSemantics | None = None,
) -> Dict[str, Any]:
    """Generate a haptic configuration informed by prompt semantics."""
    semantics = ensure_semantics(prompt, semantics)

    required = set(_as_sequence(subschema.get("required", ())))
    properties = subschema.get("properties", {})
    haptic: Dict[str, Any] = {}

    if "name" in properties or "name" in required:
        haptic["name"] = sanitize_identifier(prompt, fallback="haptic")

    if "device" in properties or "device" in required:
        haptic["device"] = _build_device(prompt, semantics)

    if "input_parameters" in properties or "input_parameters" in required:
        haptic["input_parameters"] = _build_input_parameters(semantics)

    if "description" in properties:
        haptic["description"] = f"Haptic pattern derived from prompt '{prompt}'."

    if "meta_info" in properties:
        tags = append_tags(semantics.tags, ("haptic",))
        haptic["meta_info"] = {"tags": tags}

    return haptic


def _build_device(prompt: str, semantics: PromptSemantics) -> Dict[str, Any]:
    device_type = "generic"
    lowered = prompt.lower()
    for keyword, mapped in _DEVICE_KEYWORDS.items():
        if keyword in lowered:
            device_type = mapped
            break

    intensity_value = amplitude_from_intensity(semantics, default=0.75)
    duration_ms = duration_from_semantics(semantics, default_ms=420.0)

    options = {
        "intensity": {
            "value": round(intensity_value, 3),
            "unit": "ratio",
        },
        "duration": {
            "value": round(duration_ms, 1),
            "unit": "ms",
        },
        "pattern": {
            "value": 3 if intensity_value > 0.7 else 2,
            "unit": "steps",
        },
    }

    return {
        "type": device_type,
        "options": options,
    }


def _build_input_parameters(semantics: PromptSemantics) -> List[Dict[str, Any]]:
    intensity_value = amplitude_from_intensity(semantics, default=0.75)
    duration_ms = duration_from_semantics(semantics, default_ms=420.0)
    return [
        {
            "name": "Pulse Intensity",
            "parameter": "intensity",
            "path": "device.options.intensity.value",
            "type": "float",
            "unit": "ratio",
            "default": round(intensity_value, 3),
            "min": 0.1,
            "max": 1.0,
        },
        {
            "name": "Pulse Duration",
            "parameter": "duration",
            "path": "device.options.duration.value",
            "type": "float",
            "unit": "ms",
            "default": round(duration_ms, 1),
            "min": 50.0,
            "max": 2000.0,
        },
    ]


def _as_sequence(value: Any):
    if isinstance(value, (list, tuple)):
        return value
    if value is None:
        return ()
    return (value,)


__all__ = ["build_haptic"]
