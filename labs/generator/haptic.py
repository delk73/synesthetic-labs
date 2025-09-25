"""Haptic component generator."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Optional

_INPUT_PARAMETERS: list[Dict[str, Any]] = [
    {
        "parameter": "haptic.intensity",
        "type": "normalized",
        "label": "Haptic intensity",
        "description": "Relative output strength for the haptic device.",
        "minimum": 0.0,
        "maximum": 1.0,
        "default": 0.35,
        "step": 0.01,
    },
    {
        "parameter": "haptic.frequency",
        "type": "hertz",
        "label": "Haptic frequency",
        "description": "Carrier vibration frequency in hertz.",
        "minimum": 10.0,
        "maximum": 400.0,
        "default": 120.0,
        "step": 1.0,
    },
]

_DEFAULT_PROFILE: Dict[str, Any] = {
    "waveform": "sine",
    "intensity": 0.35,
    "frequency": 120.0,
}


class HapticGenerator:
    """Generate the baseline haptic configuration."""

    def __init__(self, *, version: str = "v0.2") -> None:
        self.version = version

    def generate(self, *, seed: Optional[int] = None) -> Dict[str, Any]:
        """Return the haptic component payload."""

        return {
            "component": "haptic",
            "version": self.version,
            "device": "generic",
            "description": "Generic haptic device with intensity and frequency parameters.",
            "profile": deepcopy(_DEFAULT_PROFILE),
            "input_parameters": deepcopy(_INPUT_PARAMETERS),
        }
