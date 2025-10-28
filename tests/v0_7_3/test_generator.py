"""
Generator tests for schema version 0.7.3.
Tests that generated assets pass MCP validation.
"""

import pytest
from labs.v0_7_3.generator import generate_asset
from labs.mcp.client import MCPClient


def test_minimal_generator_produces_valid_asset():
    """Minimal generator (no LLM) produces MCP-valid assets."""
    asset = generate_asset("test shader", use_llm=False)
    
    # Verify structure
    assert "$schema" in asset
    assert "name" in asset
    assert asset["name"] == "test_shader"
    
    # Validate via MCP
    client = MCPClient(schema_version="0.7.3")
    result = client.confirm(asset, strict=True)
    
    assert result["ok"] is True


def test_generator_sanitizes_names():
    """Generator converts prompts to valid asset names."""
    asset = generate_asset("Red Pulsing Shader!!! (animated)", use_llm=False)
    
    # Name should be sanitized
    assert asset["name"] == "red_pulsing_shader_animated"
    
    # Should still validate
    client = MCPClient(schema_version="0.7.3")
    result = client.confirm(asset, strict=True)
    assert result["ok"] is True


def test_generator_includes_schema_field():
    """Generated assets include $schema field."""
    asset = generate_asset("test", use_llm=False)
    
    assert "$schema" in asset
    assert "0.7.3" in asset["$schema"]
    assert "synesthetic-asset.schema.json" in asset["$schema"]


@pytest.mark.skipif(
    not pytest.importorskip("openai", reason="openai not installed"),
    reason="OpenAI package not available"
)
def test_azure_generator_requires_credentials():
    """Azure generator raises error if credentials missing."""
    import os
    
    # Save original
    original = os.environ.get("AZURE_OPENAI_API_KEY")
    
    try:
        # Remove credentials
        os.environ.pop("AZURE_OPENAI_API_KEY", None)
        
        # Should raise ValueError
        with pytest.raises(ValueError, match="AZURE_OPENAI_API_KEY"):
            generate_asset("test", use_llm=True, engine="azure")
    finally:
        # Restore
        if original:
            os.environ["AZURE_OPENAI_API_KEY"] = original


@pytest.mark.skipif(
    not pytest.importorskip("openai", reason="openai not installed"),
    reason="OpenAI package not available"
)
def test_azure_generator_validates():
    """Azure-generated assets pass MCP validation."""
    import os
    
    if not os.getenv("AZURE_OPENAI_API_KEY"):
        pytest.skip("Azure credentials not available")
    
    asset = generate_asset(
        "red pulsing shader",
        use_llm=True,
        engine="azure"
    )
    
    # Validate via MCP
    client = MCPClient(schema_version="0.7.3")
    result = client.confirm(asset, strict=True)
    
    assert result["ok"] is True
    assert asset["name"]  # Has content
