"""Tone component generator."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Optional

_INPUT_PARAMETERS: list[Dict[str, Any]] = [
    {
        "parameter": "tone.volume",
        "type": "decibel",
        "label": "Synth volume",
        "description": "Overall gain staging for the synth output.",
        "minimum": -60.0,
        "maximum": 0.0,
        "default": -12.0,
        "step": 0.5,
    },
    {
        "parameter": "tone.detune",
        "type": "cents",
        "label": "Oscillator detune",
        "description": "Fine tune offset applied to the oscillator.",
        "minimum": -120.0,
        "maximum": 120.0,
        "default": 0.0,
        "step": 1.0,
    },
    {
        "parameter": "tone.portamento",
        "type": "seconds",
        "label": "Portamento",
        "description": "Glide time between subsequent notes.",
        "minimum": 0.0,
        "maximum": 1.0,
        "default": 0.05,
        "step": 0.01,
    },
]

_ENVELOPE: Dict[str, Any] = {
    "attack": 0.05,
    "decay": 0.2,
    "sustain": 0.7,
    "release": 0.8,
}

_EFFECTS: list[Dict[str, Any]] = [
    {
        "id": "room_reverb",
        "type": "reverb",
        "wet": 0.2,
        "decay": 1.5,
    }
]


class ToneGenerator:
    """Generate the canonical Tone.Synth configuration."""

    def __init__(self, *, version: str = "v0.2") -> None:
        self.version = version

    def generate(self, *, seed: Optional[int] = None) -> Dict[str, Any]:
        """Return the tone component payload."""

        return {
            "component": "tone",
            "version": self.version,
            "name": "Baseline Synth",
            "engine": "Tone.Synth",
            "description": "Canonical Tone.Synth baseline with envelope and reverb.",
            "settings": {
                "volume": -12.0,
                "detune": 0.0,
                "portamento": 0.05,
                "envelope": deepcopy(_ENVELOPE),
            },
            "effects": deepcopy(_EFFECTS),
            "input_parameters": deepcopy(_INPUT_PARAMETERS),
        }
