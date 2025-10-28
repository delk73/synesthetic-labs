"""Tone component builder for schema version 0.7.3."""

from __future__ import annotations

from typing import Any, Dict, List

from labs.v0_7_3.prompt_parser import PromptSemantics

from .common import (
    append_tags,
    duration_from_semantics,
    ensure_semantics,
    envelope_from_intensity,
    frequency_from_semantics,
    intensity_scalar,
    sanitize_identifier,
    tempo_from_semantics,
)

_SYNTH_BY_EFFECT = {
    "pulse": "Tone.MembraneSynth",
    "percussive": "Tone.MembraneSynth",
    "wave": "Tone.PolySynth",
    "ambient": "Tone.FMSynth",
    "drone": "Tone.DuoSynth",
    "glow": "Tone.AMSynth",
    "spiral": "Tone.PolySynth",
}

_OSCILLATOR_BY_EFFECT = {
    "pulse": "square",
    "wave": "sine",
    "ambient": "triangle",
    "drone": "sawtooth",
    "percussive": "square",
    "glow": "sine",
}

_DEFAULT_NOTES = ("C4", "Eb4", "G4", "Bb4")


def build_tone(
    prompt: str,
    subschema: Dict[str, Any],
    *,
    semantics: PromptSemantics | None = None,
) -> Dict[str, Any]:
    """Generate a Tone.js configuration informed by the prompt semantics."""
    semantics = ensure_semantics(prompt, semantics)

    required = set(_as_sequence(subschema.get("required", ())))
    properties = subschema.get("properties", {})
    tone: Dict[str, Any] = {}

    if "name" in properties or "name" in required:
        tone["name"] = sanitize_identifier(prompt, fallback="tone")

    if "synth" in properties or "synth" in required:
        tone["synth"] = _build_synth(semantics)

    if "patterns" in properties:
        tone["patterns"] = _build_patterns(semantics)

    if "parts" in properties:
        tone["parts"] = _build_parts(semantics)

    if "effects" in properties:
        tone["effects"] = [
            {
                "type": "Tone.Chorus",
                "order": 0,
                "options": {
                    "frequency": 1.5,
                    "delayTime": 2.5,
                    "depth": round(intensity_scalar(semantics, default=0.6), 2),
                },
            }
        ]

    if "meta_info" in properties:
        tags = append_tags(semantics.tags, semantics.colors)
        meta: Dict[str, Any] = {
            "category": "audio",
            "complexity": "moderate",
            "tags": tags,
        }
        if semantics.mood:
            meta["mood"] = semantics.mood
        if semantics.tempo_bpm:
            meta["tempo_bpm"] = semantics.tempo_bpm
        tone["meta_info"] = meta

    if "description" in properties:
        tone["description"] = f"Tone derived from prompt '{prompt}'."

    if "input_parameters" in properties:
        tone["input_parameters"] = _build_input_parameters(semantics)

    return tone


def _build_synth(semantics: PromptSemantics) -> Dict[str, Any]:
    effect = semantics.effects[0] if semantics.effects else None
    synth_type = _SYNTH_BY_EFFECT.get(effect, "Tone.PolySynth")
    oscillator_type = _OSCILLATOR_BY_EFFECT.get(effect, "sine")
    envelope = envelope_from_intensity(semantics)
    volume = round(-12.0 * max(0.3, intensity_scalar(semantics, default=0.7)), 2)
    frequency = frequency_from_semantics(semantics)

    return {
        "type": synth_type,
        "options": {
            "oscillator": {
                "type": oscillator_type,
                "frequency": frequency,
                "spread": 20,
            },
            "envelope": envelope,
            "volume": volume,
        },
    }


def _build_patterns(semantics: PromptSemantics) -> List[Dict[str, Any]]:
    tempo = tempo_from_semantics(semantics)
    notes = list(_DEFAULT_NOTES)
    if semantics.colors:
        seed = semantics.colors[0]
        if seed in {"red", "orange"}:
            notes = ["A3", "C4", "E4", "G4"]
        elif seed in {"blue", "teal"}:
            notes = ["D3", "F3", "A3", "C4"]
        elif seed in {"green", "yellow"}:
            notes = ["G3", "B3", "D4", "F#4"]
    return [
        {
            "id": "primary_sequence",
            "type": "sequence",
            "options": {
                "notes": notes,
                "subdivision": "4n",
                "tempo": tempo,
            },
        }
    ]


def _build_parts(semantics: PromptSemantics) -> List[Dict[str, Any]]:
    tempo = tempo_from_semantics(semantics)
    duration = "2m" if tempo < 80 else "1m"
    return [
        {
            "id": "primary_part",
            "pattern": "primary_sequence",
            "start": "0:0:0",
            "duration": duration,
            "loop": True,
        }
    ]


def _build_input_parameters(semantics: PromptSemantics) -> List[Dict[str, Any]]:
    freq = frequency_from_semantics(semantics)
    intensity = intensity_scalar(semantics, default=0.7)
    return [
        {
            "name": "Root Frequency",
            "path": "synth.options.oscillator.frequency",
            "parameter": "frequency",
            "type": "number",
            "unit": "Hz",
            "default": freq,
            "min": 40,
            "max": 4000,
        },
        {
            "name": "Tone Intensity",
            "path": "synth.options.envelope.attack",
            "parameter": "attack",
            "type": "number",
            "unit": "ratio",
            "default": round(intensity, 3),
            "min": 0.05,
            "max": 2.5,
        },
    ]


def _as_sequence(value: Any):
    if isinstance(value, (list, tuple)):
        return value
    if value is None:
        return ()
    return (value,)


__all__ = ["build_tone"]
