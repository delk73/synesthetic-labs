"""Control component builder for schema version 0.7.3."""

from __future__ import annotations

from typing import Any, Dict, List

from labs.v0_7_3.prompt_parser import PromptSemantics

from .common import (
    amplitude_from_intensity,
    append_tags,
    ensure_semantics,
    sanitize_identifier,
    tempo_from_semantics,
)


def build_control(
    prompt: str,
    subschema: Dict[str, Any],
    *,
    semantics: PromptSemantics | None = None,
) -> Dict[str, Any]:
    """Generate control mappings that adjust shader and tone behaviour."""
    semantics = ensure_semantics(prompt, semantics)

    required = set(_as_sequence(subschema.get("required", ())))
    properties = subschema.get("properties", {})
    control: Dict[str, Any] = {}

    if "name" in properties or "name" in required:
        control["name"] = sanitize_identifier(prompt, fallback="control")

    if "control_parameters" in properties or "control_parameters" in required:
        control["control_parameters"] = _build_control_parameters(semantics)

    if "meta_info" in properties:
        control["meta_info"] = {
            "tags": append_tags(semantics.tags, ("control", "interaction")),
        }

    if "description" in properties:
        control["description"] = f"Interactive controls derived from prompt '{prompt}'."

    return control


def _build_control_parameters(semantics: PromptSemantics) -> List[Dict[str, Any]]:
    tempo = tempo_from_semantics(semantics, default=72.0)
    intensity = amplitude_from_intensity(semantics, default=0.75)
    return [
        {
            "parameter": "shader.uniforms.u_time",
            "label": "Animation Speed",
            "type": "float",
            "unit": "ratio",
            "default": round(tempo / 60.0, 2),
            "min": 0.25,
            "max": 4.0,
            "mappings": [
                {
                    "combo": {
                        "keys": ["Shift"],
                        "mouseButtons": ["left"],
                        "strict": False,
                        "wheel": None,
                    },
                    "action": {
                        "axis": "mouse.y",
                        "sensitivity": 0.35,
                        "curve": "linear",
                        "scale": 1.0,
                    },
                }
            ],
        },
        {
            "parameter": "tone.synth.options.volume",
            "label": "Tone Volume",
            "type": "float",
            "unit": "db",
            "default": -12.0,
            "min": -48.0,
            "max": 0.0,
            "mappings": [
                {
                    "combo": {
                        "keys": ["Ctrl"],
                        "mouseButtons": None,
                        "strict": False,
                        "wheel": True,
                    },
                    "action": {
                        "axis": "mouse.wheel",
                        "sensitivity": 0.5,
                        "curve": "linear",
                        "scale": 1.0,
                    },
                }
            ],
        },
        {
            "parameter": "haptic.device.options.intensity.value",
            "label": "Haptic Intensity",
            "type": "float",
            "unit": "ratio",
            "default": round(intensity, 2),
            "min": 0.1,
            "max": 1.0,
            "mappings": [
                {
                    "combo": {
                        "keys": ["Alt"],
                        "mouseButtons": ["left"],
                        "strict": False,
                        "wheel": None,
                    },
                    "action": {
                        "axis": "mouse.x",
                        "sensitivity": 0.45,
                        "curve": "sine",
                        "scale": 1.0,
                    },
                }
            ],
        },
    ]


def _as_sequence(value: Any):
    if isinstance(value, (list, tuple)):
        return value
    if value is None:
        return ()
    return (value,)


__all__ = ["build_control"]
