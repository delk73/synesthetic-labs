"""Control component generator."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Optional

_MAPPINGS: list[Dict[str, Any]] = [
    {
        "id": "mouse_x_shader_px",
        "input": {"device": "mouse", "control": "x"},
        "parameter": "shader.u_px",
        "mode": "absolute",
        "curve": "linear",
        "range": {"minimum": -1.0, "maximum": 1.0},
    },
    {
        "id": "mouse_y_shader_py",
        "input": {"device": "mouse", "control": "y"},
        "parameter": "shader.u_py",
        "mode": "absolute",
        "curve": "linear",
        "range": {"minimum": -1.0, "maximum": 1.0},
        "invert": True,
    },
]


class ControlGenerator:
    """Generate default interaction controls."""

    def __init__(self, *, version: str = "v0.2") -> None:
        self.version = version

    def generate(self, *, seed: Optional[int] = None) -> Dict[str, Any]:
        """Return the control mapping payload."""

        return {
            "component": "control",
            "version": self.version,
            "mappings": deepcopy(_MAPPINGS),
        }
