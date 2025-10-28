"""Component builder registry for schema version 0.7.3."""

from __future__ import annotations

from typing import Any, Dict, Protocol, runtime_checkable

from labs.v0_7_3.prompt_parser import PromptSemantics

from .control import build_control
from .haptic import build_haptic
from .modulation import build_modulations
from .rule_bundle import build_rule_bundle
from .shader import build_shader
from .tone import build_tone


@runtime_checkable
class Builder(Protocol):
    """Protocol implemented by component builders."""

    def __call__(
        self,
        prompt: str,
        subschema: Dict[str, Any],
        *,
        semantics: PromptSemantics | None = None,
    ) -> Any:
        ...

BUILDERS: Dict[str, Builder] = {
    "shader": build_shader,
    "tone": build_tone,
    "haptic": build_haptic,
    "control": build_control,
    "modulations": build_modulations,
    "rule_bundle": build_rule_bundle,
}


def get_builder(name: str) -> Builder | None:
    """Return the builder callable for *name* if registered."""
    return BUILDERS.get(name)


__all__ = ["BUILDERS", "Builder", "build_shader", "get_builder"]
