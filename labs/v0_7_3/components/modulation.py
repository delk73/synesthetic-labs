"""Modulation component builder for schema version 0.7.3."""

from __future__ import annotations

from typing import Any, Dict, List

from labs.v0_7_3.prompt_parser import PromptSemantics

from .common import (
    amplitude_from_intensity,
    ensure_semantics,
    sanitize_identifier,
    tempo_from_semantics,
)


def build_modulations(
    prompt: str,
    subschema: Dict[str, Any],
    *,
    semantics: PromptSemantics | None = None,
    metadata: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    """Generate temporal modulations aligned with prompt tempo."""
    semantics = ensure_semantics(prompt, semantics)

    frequency_hz = tempo_from_semantics(semantics) / 60.0
    amplitude = amplitude_from_intensity(semantics, default=0.75)
    base_id = sanitize_identifier(prompt, fallback="modulation")

    modulation = {
        "id": f"{base_id}_tempo",
        "target": "shader.uniforms.u_time",
        "type": "additive",
        "waveform": "sine",
        "frequency": round(max(0.1, frequency_hz), 3),
        "amplitude": round(amplitude, 3),
        "offset": 0.5,
        "phase": 0.0,
        "scale": 1.0,
        "scaleProfile": "linear",
        "min": 0.0,
        "max": 1.0,
    }

    secondary = {
        "id": f"{base_id}_tone",
        "target": "tone.synth.options.envelope.attack",
        "type": "multiplicative",
        "waveform": "triangle",
        "frequency": round(max(0.05, frequency_hz / 2.0), 3),
        "amplitude": round(max(0.1, amplitude / 2.0), 3),
        "offset": 0.3,
        "phase": 0.0,
        "scale": 1.0,
        "scaleProfile": "sine",
        "min": 0.1,
        "max": 2.0,
    }

    return [modulation, secondary]


__all__ = ["build_modulations"]
