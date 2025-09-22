"""Canonical shader component generator."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Optional

_FRAGMENT_SHADER = (
    "uniform vec2 u_resolution;\n"
    "uniform float u_time;\n"
    "uniform float u_px;\n"
    "uniform float u_py;\n"
    "uniform float u_r;\n\n"
    "float circleSDF(vec2 p, float r) {\n"
    "  return length(p) - r;\n"
    "}\n\n"
    "void main() {\n"
    "  vec2 st = (gl_FragCoord.xy / u_resolution.xy) * 2.0 - 1.0;\n"
    "  st.x *= u_resolution.x / u_resolution.y;\n"
    "  vec2 p = st - vec2(u_px, u_py);\n"
    "  float d = circleSDF(p, u_r);\n"
    "  float c = 1.0 - smoothstep(-0.01, 0.01, d);\n"
    "  gl_FragColor = vec4(vec3(c), 1.0);\n"
    "}\n"
)

_UNIFORMS: list[Dict[str, Any]] = [
    {"name": "u_resolution", "type": "vec2", "description": "Viewport resolution."},
    {"name": "u_time", "type": "float", "default": 0.0, "description": "Elapsed time in seconds."},
    {
        "name": "u_px",
        "type": "float",
        "default": 0.0,
        "description": "Normalized X offset for the circle center.",
    },
    {
        "name": "u_py",
        "type": "float",
        "default": 0.0,
        "description": "Normalized Y offset for the circle center.",
    },
    {
        "name": "u_r",
        "type": "float",
        "default": 0.35,
        "description": "Circle radius in normalized coordinates.",
    },
]

_INPUT_PARAMETERS: list[Dict[str, Any]] = [
    {
        "parameter": "shader.u_px",
        "type": "float",
        "label": "Circle center X",
        "description": "Controls the normalized horizontal offset of the circle.",
        "minimum": -1.0,
        "maximum": 1.0,
        "default": 0.0,
        "step": 0.01,
        "uniform": "u_px",
    },
    {
        "parameter": "shader.u_py",
        "type": "float",
        "label": "Circle center Y",
        "description": "Controls the normalized vertical offset of the circle.",
        "minimum": -1.0,
        "maximum": 1.0,
        "default": 0.0,
        "step": 0.01,
        "uniform": "u_py",
    },
    {
        "parameter": "shader.u_r",
        "type": "float",
        "label": "Circle radius",
        "description": "Controls the circle radius in normalized units.",
        "minimum": 0.05,
        "maximum": 0.9,
        "default": 0.35,
        "step": 0.01,
        "uniform": "u_r",
    },
]


class ShaderGenerator:
    """Generate the canonical CircleSDF shader component."""

    def __init__(self, *, version: str = "v0.1") -> None:
        self.version = version

    def generate(self, *, seed: Optional[int] = None) -> Dict[str, Any]:
        """Return the shader component payload."""

        return {
            "component": "shader",
            "version": self.version,
            "name": "CircleSDF",
            "description": "Minimal circle signed distance field shader.",
            "language": "glsl",
            "sources": {"fragment": _FRAGMENT_SHADER},
            "uniforms": deepcopy(_UNIFORMS),
            "input_parameters": deepcopy(_INPUT_PARAMETERS),
        }
