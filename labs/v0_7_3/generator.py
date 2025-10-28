"""Asset generator for schema version 0.7.3."""

from typing import Any, Dict, Optional

from labs.mcp.client import load_schema_bundle
from labs.v0_7_3.components import BUILDERS
from labs.v0_7_3.schema_analyzer import SchemaAnalyzer


def generate_asset(
    prompt: str,
    *,
    version: str = "0.7.3",
    use_llm: bool = False,
    engine: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate a synesthetic asset for version 0.7.3.
    
    Args:
        prompt: User prompt describing the desired asset
        version: Schema version (default: "0.7.3")
        use_llm: Whether to use LLM generation (requires Azure config)
        engine: LLM engine to use ("azure", "gemini", etc.)
        
    Returns:
        Generated asset (MCP-validated structure)
    """
    if use_llm:
        if engine == "azure":
            return _generate_with_azure(prompt, version)
        else:
            raise ValueError(f"Unsupported LLM engine: {engine}")
    else:
        return _generate_minimal(prompt, version)


def _generate_minimal(prompt: str, version: str) -> Dict[str, Any]:
    """
    Generate minimal valid asset using schema structure.
    No LLM - pure schema-driven construction.
    """
    # Fetch schema to understand structure
    schema_bundle = load_schema_bundle(version=version)
    analyzer = SchemaAnalyzer(version=version, schema=schema_bundle)
    required = schema_bundle.get("required", [])
    properties = schema_bundle.get("properties", {})
    
    # Build minimal valid asset
    asset: Dict[str, Any] = {
        "$schema": f"https://delk73.github.io/synesthetic-schemas/schema/{version}/synesthetic-asset.schema.json"
    }
    
    # Add required fields
    for field in required:
        if field == "name":
            # Use prompt as name (sanitized)
            asset["name"] = _sanitize_name(prompt)
        elif field in properties:
            # Add minimal valid value for required field
            asset[field] = _minimal_value_for_property(properties[field])
    
    # Add meta_info (common field)
    if "meta_info" in properties and "meta_info" not in asset:
        asset["meta_info"] = {"description": prompt}

    _populate_components(asset, prompt, analyzer)
    
    return asset


def _generate_with_azure(prompt: str, version: str) -> Dict[str, Any]:
    """
    Generate asset via Azure OpenAI with structured output.
    Schema bundle injected as constraint.
    """
    import os
    from openai import AzureOpenAI
    import json
    
    # Check credentials
    if not os.getenv("AZURE_OPENAI_API_KEY"):
        raise ValueError("AZURE_OPENAI_API_KEY not set - cannot use Azure LLM")
    
    # Fetch live schema from MCP
    schema_bundle = load_schema_bundle(version=version)
    
    # Initialize Azure client
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
    )
    
    # Format version for schema name (underscores, not dots)
    schema_name = f"SynestheticAsset_{version.replace('.', '_')}"
    
    # Generate with structured output
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
        messages=[
            {
                "role": "system",
                "content": "You are a synesthetic asset generator. Generate JSON conforming to the schema."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": schema_name,
                "schema": schema_bundle,
                "strict": True
            }
        },
        temperature=0  # Deterministic
    )
    
    # Parse generated JSON
    asset = json.loads(response.choices[0].message.content)
    return asset


def _sanitize_name(prompt: str) -> str:
    """Convert prompt to valid asset name."""
    # Take first 50 chars, replace spaces with underscores
    name = prompt[:50].strip().replace(" ", "_").lower()
    # Remove non-alphanumeric except underscores
    name = "".join(c for c in name if c.isalnum() or c == "_")
    return name or "unnamed"


def _minimal_value_for_property(prop_schema: Dict[str, Any]) -> Any:
    """Generate minimal valid value for a property schema."""
    prop_type = prop_schema.get("type")
    
    if "enum" in prop_schema:
        # Use first enum value
        return prop_schema["enum"][0]
    
    if "default" in prop_schema:
        # Use default if provided
        return prop_schema["default"]
    
    # Type-based defaults
    if prop_type == "string":
        return ""
    elif prop_type == "number" or prop_type == "integer":
        return 0
    elif prop_type == "boolean":
        return False
    elif prop_type == "array":
        return []
    elif prop_type == "object":
        # Build minimal object from required fields
        required = prop_schema.get("required", [])
        properties = prop_schema.get("properties", {})
        obj = {}
        for field in required:
            if field in properties:
                obj[field] = _minimal_value_for_property(properties[field])
        return obj
    else:
        # Unknown type - return empty object
        return {}


def _populate_components(asset: Dict[str, Any], prompt: str, analyzer: SchemaAnalyzer) -> None:
    """Populate high-value components using registered builders."""
    lower_prompt = prompt.lower()
    for name, builder in BUILDERS.items():
        if name not in analyzer.available_components():
            continue
        if not _should_generate_component(name, lower_prompt):
            continue
        component_schema = analyzer.get_component_schema(name)
        component = builder(prompt, component_schema.schema)
        if component_schema.nullable and component is None:
            continue
        if component is None:
            continue
        asset[name] = component


def _should_generate_component(name: str, lower_prompt: str) -> bool:
    """Determine whether to generate component *name* for *lower_prompt*."""
    if name == "shader":
        return any(token in lower_prompt for token in ("shader", "glsl", "visual", "fragment", "vertex"))
    return False


__all__ = ["generate_asset"]
