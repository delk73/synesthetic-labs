"""Component builder registry for schema version 0.7.3."""

from __future__ import annotations

from typing import Any, Callable, Dict

from .shader import build_shader

Builder = Callable[[str, Dict[str, Any]], Dict[str, Any]]

BUILDERS: Dict[str, Builder] = {
    "shader": build_shader,
}


def get_builder(name: str) -> Builder | None:
    """Return the builder callable for *name* if registered."""
    return BUILDERS.get(name)


__all__ = ["BUILDERS", "Builder", "build_shader", "get_builder"]
