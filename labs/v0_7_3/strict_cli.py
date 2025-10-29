"""CLI for Phase 8 strict-mode component generation.

This command generates a single component (control, modulation, shader)
using the Azure OpenAI strict json_schema interface and validates the resulting
asset via the MCP TCP validator.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict

from labs.mcp.client import MCPClient, MCPClientError
from labs.mcp.exceptions import MCPUnavailableError
from labs.v0_7_3.llm import (
    STRICT_COMPONENTS,
    StrictGenerationError,
    llm_generate_component_strict,
)
from labs.v0_7_3.schema_analyzer import SchemaAnalyzer


try:  # pragma: no cover - imported lazily for CLI usage
    from openai import AzureOpenAI
except Exception:  # pragma: no cover - handled during CLI execution
    AzureOpenAI = None  # type: ignore


def _sanitize_name(prompt: str) -> str:
    candidate = prompt[:50].strip().replace(" ", "_").lower()
    filtered = "".join(char for char in candidate if char.isalnum() or char == "_")
    return filtered or "unnamed"


def _build_asset(
    *,
    prompt: str,
    component: str,
    component_payload: Dict[str, Any],
    descriptor: Dict[str, Any],
) -> Dict[str, Any]:
    schema = descriptor.get("schema")
    schema_id = descriptor.get("schema_id")
    if not isinstance(schema_id, str) or not schema_id:
        if isinstance(schema, dict):
            schema_id = schema.get("$id")
        if not isinstance(schema_id, str) or not schema_id:
            schema_id = "https://schemas.synesthetic-labs.ai/mcp/0.7.3/synesthetic-asset.schema.json"

    asset: Dict[str, Any] = {
        "$schema": schema_id,
        "name": _sanitize_name(prompt),
        component: component_payload,
    }
    return asset


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a single Synesthetic Labs component via Phase 8 strict mode",
    )
    parser.add_argument(
        "prompt",
        help="Prompt describing the desired component",
    )
    parser.add_argument(
        "--component",
        choices=sorted(STRICT_COMPONENTS),
        required=True,
        help="Component to generate strictly (control/modulation/shader)",
    )
    parser.add_argument(
        "--version",
        default="0.7.3",
        help="Schema version to target (default: 0.7.3)",
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip MCP validation of the generated payload",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Optional output file to write the component JSON",
    )

    args = parser.parse_args(argv)

    if AzureOpenAI is None:
        parser.error("openai package with AzureOpenAI client is required")

    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    if not api_key:
        parser.error("AZURE_OPENAI_API_KEY must be set")

    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    if not endpoint:
        parser.error("AZURE_OPENAI_ENDPOINT must be set")

    model = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    if not model:
        parser.error("AZURE_OPENAI_DEPLOYMENT must be set")

    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")

    azure = AzureOpenAI(
        api_key=api_key,
        azure_endpoint=endpoint,
        api_version=api_version,
    )

    client = MCPClient(schema_version=args.version)

    try:
        descriptor = client.fetch_schema("synesthetic-asset", version=args.version)
    except MCPUnavailableError as exc:
        parser.error(f"Failed to fetch schema from MCP: {exc}")

    schema = descriptor.get("schema")
    if not isinstance(schema, dict):
        parser.error("MCP did not return an inline schema bundle")

    analyzer = SchemaAnalyzer(version=args.version, schema=schema)
    component_schema = analyzer.get_component_schema(args.component)

    try:
        component_payload = llm_generate_component_strict(
            azure,
            model=model,
            component_name=args.component,
            subschema=component_schema.schema,
            prompt=args.prompt,
        )
    except StrictGenerationError as exc:
        print(f"✗ Strict generation failed: {exc}", file=sys.stderr)
        return 2

    asset = _build_asset(
        prompt=args.prompt,
        component=args.component,
        component_payload=component_payload,
        descriptor=descriptor,
    )

    if not args.no_validate:
        try:
            client.confirm(asset, strict=True)
        except MCPClientError as exc:
            print(f"✗ MCP validation failed: {exc}", file=sys.stderr)
            return 3

    output = json.dumps(component_payload, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(output)
        print(f"✓ Saved component to {args.output}", file=sys.stderr)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
