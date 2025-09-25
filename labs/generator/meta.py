"""Meta component generator."""

from __future__ import annotations

from typing import Dict, Optional


class MetaGenerator:
    """Generate descriptive metadata for the asset."""

    def __init__(self, *, version: str = "v0.2") -> None:
        self.version = version

    def generate(self, *, seed: Optional[int] = None) -> Dict[str, object]:
        """Return the meta section payload."""

        return {
            "component": "meta",
            "version": self.version,
            "title": "Circle Interaction Baseline",
            "description": (
                "Canonical multimodal baseline featuring a CircleSDF shader, "
                "Tone.Synth audio bed, and haptic pulse cues."
            ),
            "category": "multimodal",
            "complexity": "medium",
            "tags": ["circle", "baseline"],
        }
