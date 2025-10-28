"""Rule bundle builder for schema version 0.7.3."""

from __future__ import annotations

from typing import Any, Dict, List

from labs.v0_7_3.prompt_parser import PromptSemantics

from .common import append_tags, ensure_semantics, sanitize_identifier, tempo_from_semantics


def build_rule_bundle(
    prompt: str,
    subschema: Dict[str, Any],
    *,
    semantics: PromptSemantics | None = None,
) -> Dict[str, Any]:
    """Generate a minimal rule bundle linking modulation to shader tempo."""
    semantics = ensure_semantics(prompt, semantics)

    required = set(_as_sequence(subschema.get("required", ())))
    properties = subschema.get("properties", {})
    name = sanitize_identifier(prompt, fallback="rule_bundle")

    bundle: Dict[str, Any] = {}

    if "name" in properties or "name" in required:
        bundle["name"] = name

    if "description" in properties:
        bundle["description"] = f"Rule bundle derived from prompt '{prompt}'."

    rules = _build_rules(name, semantics)

    if "rules" in properties or "rules" in required:
        bundle["rules"] = rules

    if "meta_info" in properties:
        bundle["meta_info"] = {
            "tags": append_tags(semantics.tags, ("rule", "automation")),
            "tempo_reference": tempo_from_semantics(semantics),
        }

    return bundle


def _build_rules(name: str, semantics: PromptSemantics) -> List[Dict[str, Any]]:
    tempo = tempo_from_semantics(semantics)
    amplitude_threshold = 0.7
    rule_id = f"{name}_tempo_rule"

    return [
        {
            "id": rule_id,
            "expr": {
                "op": ">",
                "left": {"path": "modulations[0].amplitude"},
                "right": amplitude_threshold,
            },
            "target": "shader.uniforms.u_time",
            "trigger": {
                "type": "tempo",
                "bpm": tempo,
                "condition": "external >= prompt",
            },
            "effects": [
                {
                    "type": "scale",
                    "value": 1.1,
                }
            ],
        }
    ]


def _as_sequence(value: Any):
    if isinstance(value, (list, tuple)):
        return value
    if value is None:
        return ()
    return (value,)


__all__ = ["build_rule_bundle"]
