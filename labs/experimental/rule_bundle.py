"""Rule bundle component generator (experimental)."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Optional

_RULES: list[Dict[str, Any]] = [
    {
        "id": "grid_press_primary",
        "name": "Grid press multimodal response",
        "trigger": {
            "type": "grid_press",
            "grid": "main",
            "cells": "*",
        },
        "effects": [
            {
                "type": "audio.note",
                "note": "C4",
                "velocity": 0.8,
            },
            {
                "type": "parameter",
                "target": "tone.detune",
                "mode": "add",
                "value": 12.0,
            },
            {
                "type": "parameter",
                "target": "haptic.intensity",
                "mode": "set",
                "value": 0.85,
            },
            {
                "type": "parameter",
                "target": "shader.u_r",
                "mode": "add",
                "value": 0.05,
            },
        ],
    }
]


class RuleBundleGenerator:
    """Generate the baseline rule bundle for experimental builds."""

    def __init__(self, *, version: str = "v0.2") -> None:
        self.version = version

    def generate(self, *, seed: Optional[int] = None) -> Dict[str, Any]:
        """Return the rule bundle payload."""

        return {
            "component": "rule_bundle",
            "version": self.version,
            "name": "Default grid rule bundle",
            "grid": {"rows": 4, "columns": 4},
            "rules": deepcopy(_RULES),
        }
