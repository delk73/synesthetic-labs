"""Strict-mode Azure helpers for schema v0.7.3."""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Dict, Mapping


logger = logging.getLogger(__name__)

STRICT_COMPONENTS = frozenset({"control", "modulation", "shader"})


class StrictGenerationError(RuntimeError):
    """Raised when strict-mode generation fails."""


def generate_strict_component(
    client,
    *,
    model: str,
    component_name: str,
    subschema: Mapping[str, object],
    prompt: str,
) -> Dict[str, object]:
    """Generate a component via Azure strict json_schema output.

    Args:
        client: Azure OpenAI client (already configured).
        model: Deployment name.
        component_name: Component identifier (e.g. ``"shader"``).
        subschema: Inline JSON Schema fragment from MCP (unmodified).
        prompt: Raw prompt string provided by the caller.

    Returns:
        Parsed component payload.

    Raises:
        StrictGenerationError: If Azure returns invalid JSON or the payload is not an object.
    """

    schema_hash = hashlib.sha256(
        json.dumps(subschema, sort_keys=True).encode("utf-8")
    ).hexdigest()
    logger.info(
        "strict.event component=%s schema_sha256=%s status=start",
        component_name,
        schema_hash,
    )

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        seed=0,
        max_tokens=2048,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": component_name,
                "schema": subschema,
                "strict": True,
            },
        },
    )

    content = response.choices[0].message.content or "{}"
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive guard
        logger.error(
            "strict.event component=%s schema_sha256=%s status=invalid_json",
            component_name,
            schema_hash,
        )
        raise StrictGenerationError(f"Azure returned invalid JSON: {exc}") from exc

    if not isinstance(payload, dict):
        logger.error(
            "strict.event component=%s schema_sha256=%s status=non_object",
            component_name,
            schema_hash,
        )
        raise StrictGenerationError("Azure strict generation must return a JSON object")

    logger.info(
        "strict.event component=%s schema_sha256=%s status=success",
        component_name,
        schema_hash,
    )
    return payload


def llm_generate_component_strict(
    client,
    *,
    model: str,
    component_name: str,
    subschema: Mapping[str, object],
    prompt: str,
) -> Dict[str, object]:
    """Public alias for strict-mode generation limited to Phase 8 components."""

    if component_name not in STRICT_COMPONENTS:
        raise ValueError(
            f"Component '{component_name}' is outside strict-mode scope: {sorted(STRICT_COMPONENTS)}"
        )
    return generate_strict_component(
        client,
        model=model,
        component_name=component_name,
        subschema=subschema,
        prompt=prompt,
    )


__all__ = [
    "STRICT_COMPONENTS",
    "StrictGenerationError",
    "generate_strict_component",
    "llm_generate_component_strict",
]
