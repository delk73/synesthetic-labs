"""Azure OpenAI helpers for component-oriented generation (schema v0.7.3)."""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, Mapping, Optional

from labs.v0_7_3.prompt_parser import PromptSemantics, parse_prompt

PromptPlan = Dict[str, Any]

logger = logging.getLogger(__name__)

AZURE_STRICT_ALLOW = {"shader", "modulation"}
AZURE_STRICT_BLOCK = {"control", "tone", "haptic"}


def supports_azure_strict(component: str) -> bool:
    """Return True when the component is eligible for Azure strict generation."""
    return component in AZURE_STRICT_ALLOW

_DECOMPOSITION_SCHEMA: Dict[str, Any] = {
    "name": "SynestheticPromptPlan",
    "schema": {
        "type": "object",
        "properties": {
            "modality": {
                "type": "string",
                "enum": ["shader", "tone", "haptic", "control", "mixed"],
            },
            "primary_component": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "characteristics": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["type", "characteristics"],
            },
            "suggested_tags": {
                "type": "array",
                "items": {"type": "string"},
                "default": [],
            },
            "constraints": {
                "type": "object",
                "additionalProperties": True,
                "default": {},
            },
        },
        "required": ["modality", "primary_component", "suggested_tags"],
    },
}


def llm_decompose_prompt(
    client: Any,
    *,
    model: str,
    prompt: str,
) -> PromptPlan:
    """Request semantic decomposition for *prompt* via Azure OpenAI."""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You analyse creative prompts for synesthetic assets and propose "
                    "component characteristics and constraints."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        response_format={
            "type": "json_schema",
            "json_schema": _DECOMPOSITION_SCHEMA,
        },
        temperature=0,
    )
    payload = response.choices[0].message.content or "{}"
    plan = json.loads(payload)
    if not isinstance(plan, dict):
        raise ValueError("LLM decomposition payload must be a JSON object")
    return plan


def llm_generate_component(
    client: Any,
    *,
    model: str,
    component_name: str,
    subschema: Mapping[str, Any],
    prompt: str,
    plan: PromptPlan,
    fallback_semantics: Optional[PromptSemantics] = None,
) -> Dict[str, Any]:
    """Call Azure OpenAI to generate a component matching *subschema*."""
    schema_name = f"Synesthetic_{component_name.title().replace('_', '')}"
    semantics = fallback_semantics or parse_prompt(prompt)

    messages = [
        {
            "role": "system",
            "content": (
                "You generate structured component JSON for synesthetic assets. "
                "Strictly follow the provided JSON schema."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "prompt": prompt,
                    "component": component_name,
                    "plan": plan,
                    "semantics": semantics.to_dict(),
                },
                indent=2,
            ),
        },
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={
            "type": "json_schema",
            "json_schema": {"name": schema_name, "schema": subschema},
        },
        temperature=0.2,
    )
    payload = response.choices[0].message.content or "{}"
    data = json.loads(payload)
    if not isinstance(data, dict) and not isinstance(data, list):
        raise ValueError("LLM component response must be a JSON object or array")
    return data


def llm_generate_component_strict(
    client: Any,
    *,
    model: str,
    component_name: str,
    subschema: Mapping[str, Any],
    prompt: str,
    plan: PromptPlan,
) -> Dict[str, Any]:
    """
    Generate a component via Azure strict json_schema output without touching the schema.

    Returns a dict payload on success, or {} to signal fallback.
    """
    schema_name = f"Synesthetic_{component_name.title().replace('_', '')}"
    try:
        schema_hash = hashlib.sha256(
            json.dumps(subschema, sort_keys=True).encode("utf-8")
        ).hexdigest()
    except TypeError:
        # Best-effort hash even if schema contains non-JSON-native types
        schema_hash = hashlib.sha256(repr(subschema).encode("utf-8")).hexdigest()

    logger.debug(
        "azure_strict_request component=%s schema_sha256=%s",
        component_name,
        schema_hash,
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You generate structured component JSON for synesthetic assets. "
                "Strictly follow the provided JSON schema."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "prompt": prompt,
                    "component": component_name,
                    "plan": plan,
                },
                indent=2,
            ),
        },
    ]

    request_kwargs = {
        "model": model,
        "messages": messages,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": schema_name,
                "schema": subschema,
                "strict": True,
            },
        },
        "temperature": 0,
        "max_output_tokens": 2048,
        "seed": 0,
    }

    try:
        response = client.chat.completions.create(**request_kwargs)
    except TypeError as exc:
        # Some client versions do not yet expose the seed parameter
        if "seed" in str(exc):
            request_kwargs.pop("seed", None)
            response = client.chat.completions.create(**request_kwargs)
        else:
            logger.warning(
                "azure_strict_failure component=%s reason=%s", component_name, exc
            )
            return {}
    except Exception as exc:  # pragma: no cover - network failure falls back
        logger.warning(
            "azure_strict_failure component=%s reason=%s", component_name, exc
        )
        return {}

    payload = response.choices[0].message.content or "{}"
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        logger.warning(
            "azure_strict_parse_error component=%s reason=%s", component_name, exc
        )
        return {}

    if not isinstance(data, dict):
        logger.warning(
            "azure_strict_non_object component=%s type=%s",
            component_name,
            type(data).__name__,
        )
        return {}

    return data


__all__ = [
    "PromptPlan",
    "AZURE_STRICT_ALLOW",
    "AZURE_STRICT_BLOCK",
    "supports_azure_strict",
    "llm_decompose_prompt",
    "llm_generate_component",
    "llm_generate_component_strict",
]
