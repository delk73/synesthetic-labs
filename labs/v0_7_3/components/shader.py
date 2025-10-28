"""Shader component builder for schema version 0.7.3."""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, Sequence, Tuple

from labs.v0_7_3.prompt_parser import PromptSemantics, parse_prompt


ColorVector = Tuple[float, float, float]

_COLOR_TABLE: Dict[str, ColorVector] = {
    "red": (1.0, 0.0, 0.0),
    "green": (0.0, 1.0, 0.0),
    "blue": (0.0, 0.0, 1.0),
    "purple": (0.58, 0.0, 0.83),
    "magenta": (1.0, 0.0, 0.8),
    "orange": (1.0, 0.5, 0.0),
    "yellow": (1.0, 0.9, 0.0),
    "teal": (0.0, 0.8, 0.7),
    "cyan": (0.0, 1.0, 1.0),
    "white": (1.0, 1.0, 1.0),
    "black": (0.05, 0.05, 0.05),
}

_EFFECT_KEYWORDS = {
    "pulse": "pulse",
    "pulsing": "pulse",
    "heartbeat": "pulse",
    "wave": "wave",
    "oscillating": "wave",
    "spiral": "spiral",
    "glow": "glow",
}

_VERTEX_SHADER = """\
#version 330 core
layout (location = 0) in vec3 a_position;
layout (location = 1) in vec2 a_uv;

out vec2 v_uv;

void main() {
  v_uv = a_uv;
  gl_Position = vec4(a_position, 1.0);
}
"""


def build_shader(
    prompt: str,
    subschema: Dict[str, Any],
    *,
    semantics: PromptSemantics | None = None,
) -> Dict[str, Any]:
    """
    Generate a shader component that conforms to the provided *subschema*.

    The builder derives colour and animation hints from the prompt and
    injects them into a lightweight GLSL shader pair.
    """
    if not isinstance(subschema, dict):
        raise TypeError("shader subschema must be a mapping")

    required = set(_as_sequence(subschema.get("required", [])))
    properties = subschema.get("properties", {})
    if not isinstance(properties, dict):
        properties = {}

    semantics = semantics or parse_prompt(prompt)

    color_name, color_vec = _extract_dominant_color(semantics)
    effect = _infer_effect(semantics)
    tags = _derive_tags(prompt, semantics, color_name, effect)

    shader: Dict[str, Any] = {}

    if "name" in properties or "name" in required:
        shader["name"] = _derive_shader_name(prompt, fallback=color_name or "procedural")

    if "vertex_shader" in properties or "vertex_shader" in required:
        shader["vertex_shader"] = _VERTEX_SHADER.strip()

    if "fragment_shader" in properties or "fragment_shader" in required:
        shader["fragment_shader"] = _build_fragment_shader(color_vec, effect, tags)

    if "description" in properties:
        shader["description"] = _build_description(prompt, color_name, effect)

    if "meta_info" in properties:
        meta_info: Dict[str, Any] = {
            "source_prompt": prompt,
            "tags": list(tags) if tags else [],
        }
        if semantics.mood:
            meta_info["mood"] = semantics.mood
        if semantics.intensity:
            meta_info["intensity"] = semantics.intensity
        if tags:
            meta_info["tags"] = list(tags)
        shader["meta_info"] = meta_info

    if "uniforms" in properties:
        shader["uniforms"] = [
            {
                "name": "u_time",
                "type": "float",
                "stage": "fragment",
                "default": 0.0,
            }
        ]

    if "input_parameters" in properties:
        shader["input_parameters"] = None

    return shader


# Internal helpers -----------------------------------------------------

def _extract_dominant_color(semantics: PromptSemantics) -> Tuple[str | None, ColorVector]:
    for name in semantics.colors:
        if name in _COLOR_TABLE:
            return name, _COLOR_TABLE[name]
    lowered = semantics.raw.lower()
    for name, vector in _COLOR_TABLE.items():
        if name in lowered:
            return name, vector
    return None, (0.8, 0.8, 0.8)


def _infer_effect(semantics: PromptSemantics) -> str:
    if semantics.effects:
        return semantics.effects[0]
    lowered = semantics.raw.lower()
    for keyword, effect in _EFFECT_KEYWORDS.items():
        if keyword in lowered:
            return effect
    return "static"


def _derive_tags(
    prompt: str,
    semantics: PromptSemantics,
    color: str | None,
    effect: str,
) -> Sequence[str]:
    tags = list(semantics.tags)
    if color:
        tags.append(color)
    if effect != "static":
        tags.append(effect)
    if "shader" in prompt.lower():
        tags.append("shader")
    if "glsl" in prompt.lower():
        tags.append("glsl")
    seen = set()
    unique = []
    for tag in tags:
        if tag in seen:
            continue
        seen.add(tag)
        unique.append(tag)
    return unique


_NAME_SANITISER = re.compile(r"[^a-z0-9_]+")


def _derive_shader_name(prompt: str, *, fallback: str) -> str:
    candidate = prompt.strip().lower().replace(" ", "_")
    candidate = _NAME_SANITISER.sub("_", candidate)
    candidate = candidate.strip("_") or fallback
    return candidate[:60]


def _build_description(prompt: str, color: str | None, effect: str) -> str:
    pieces = []
    if color:
        pieces.append(f"{color} colour palette")
    if effect != "static":
        pieces.append(f"{effect} animation")
    if pieces:
        return f"Shader derived from prompt '{prompt}' featuring " + " and ".join(pieces) + "."
    return f"Shader derived from prompt '{prompt}'."


def _build_fragment_shader(color: ColorVector, effect: str, tags: Sequence[str]) -> str:
    r, g, b = (f"{component:.3f}" for component in color)
    animation_block = _fragment_animation_block(effect)
    tags_comment = f"// tags: {', '.join(tags)}\n" if tags else ""
    return (
        "#version 330 core\n"
        "uniform float u_time;\n"
        "in vec2 v_uv;\n"
        "out vec4 fragColor;\n\n"
        f"{tags_comment}"
        "void main() {\n"
        f"{animation_block}"
        f"  vec3 baseColor = vec3({r}, {g}, {b});\n"
        "  fragColor = vec4(baseColor * pulse, 1.0);\n"
        "}\n"
    )


def _fragment_animation_block(effect: str) -> str:
    if effect == "pulse":
        return "  float pulse = 0.5 + 0.5 * sin(u_time * 6.2831);\n"
    if effect == "wave":
        return "  float pulse = 0.5 + 0.5 * sin(u_time + v_uv.x * 6.2831);\n"
    if effect == "spiral":
        return (
            "  vec2 centred = v_uv - 0.5;\n"
            "  float angle = atan(centred.y, centred.x) + u_time;\n"
            "  float radius = length(centred);\n"
            "  float pulse = 0.5 + 0.5 * sin(angle * 4.0 + radius * 12.0);\n"
        )
    if effect == "glow":
        return "  float pulse = 0.75 + 0.25 * sin(u_time * 3.0);\n"
    return "  float pulse = 1.0;\n"


def _as_sequence(value: Any) -> Iterable[Any]:
    if isinstance(value, (list, tuple)):
        return value
    if value is None:
        return ()
    return (value,)


__all__ = ["build_shader"]
