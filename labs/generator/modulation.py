"""Modulation component generator."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Optional

_MODULATORS: list[Dict[str, Any]] = [
    {
        "id": "shader_radius_triangle_lfo",
        "type": "lfo",
        "waveform": "triangle",
        "rate_hz": 0.2,
        "depth": 0.1,
        "offset": 0.0,
        "target": "shader.u_r",
    },
    {
        "id": "haptic_intensity_sine_lfo",
        "type": "lfo",
        "waveform": "sine",
        "rate_hz": 0.8,
        "depth": 0.25,
        "offset": 0.35,
        "target": "haptic.intensity",
    },
    {
        "id": "tone_detune_triangle_lfo",
        "type": "lfo",
        "waveform": "triangle",
        "rate_hz": 0.1,
        "depth": 5.0,
        "offset": 0.0,
        "target": "tone.detune",
    },
]


class ModulationGenerator:
    """Generate baseline modulation sources."""

    def __init__(self, *, version: str = "v0.2") -> None:
        self.version = version

    def generate(self, *, seed: Optional[int] = None) -> Dict[str, Any]:
        """Return the modulation payload."""

        return {
            "component": "modulation",
            "version": self.version,
            "modulators": deepcopy(_MODULATORS),
        }
