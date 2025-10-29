"""
Generator tests for schema version 0.7.3.
Tests that generated assets pass MCP validation.
"""

import importlib.util
import os

import pytest
from labs.v0_7_3.generator import generate_asset
from labs.mcp.client import MCPClient

OPENAI_AVAILABLE = importlib.util.find_spec("openai") is not None
AZURE_ENV_READY = OPENAI_AVAILABLE and all(
    os.getenv(env_var) for env_var in ("AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT")
)


def test_minimal_generator_produces_valid_asset():
    """Minimal generator (no LLM) produces MCP-valid assets."""
    asset = generate_asset("test shader", use_llm=False)
    
    # Verify structure
    assert "$schema" in asset
    assert "name" in asset
    assert asset["name"] == "test_shader"
    assert "shader" in asset
    assert asset["shader"]["fragment_shader"]
    assert "vec3" in asset["shader"]["fragment_shader"]
    assert asset["meta_info"]["description"] == "test shader"
    
    # Validate via MCP
    client = MCPClient(schema_version="0.7.3")
    result = client.confirm(asset, strict=True)
    
    assert result["ok"] is True


def test_generator_sanitizes_names():
    """Generator converts prompts to valid asset names."""
    asset = generate_asset("Red Pulsing Shader!!! (animated)", use_llm=False)
    
    # Name should be sanitized
    assert asset["name"] == "red_pulsing_shader_animated"
    assert "shader" in asset
    assert "pulse" in asset["shader"]["fragment_shader"].lower()
    assert "red" in asset["shader"]["fragment_shader"].lower()
    
    # Should still validate
    client = MCPClient(schema_version="0.7.3")
    result = client.confirm(asset, strict=True)
    assert result["ok"] is True


def test_generator_populates_multimodal_components():
    """Generator populates tone, haptic, control, and modulations when requested."""
    prompt = "red pulsing shader with 60 BPM heartbeat rhythm, ambient tone at 440Hz and haptic vibration"
    asset = generate_asset(prompt, use_llm=False)

    assert "tone" in asset
    assert asset["tone"]["synth"]["type"].startswith("Tone.")
    assert "haptic" in asset
    assert asset["haptic"]["device"]["options"]
    assert "control" in asset
    assert "modulations" in asset
    assert isinstance(asset["modulations"], list)
    assert asset["modulations"][0]["frequency"] > 0

    client = MCPClient(schema_version="0.7.3")
    result = client.confirm(asset, strict=True)
    assert result["ok"] is True


def test_generator_includes_schema_field():
    """Generated assets include $schema field."""
    asset = generate_asset("test", use_llm=False)
    
    assert "$schema" in asset
    assert "0.7.3" in asset["$schema"]
    assert "synesthetic-asset.schema.json" in asset["$schema"]


@pytest.mark.skipif(not OPENAI_AVAILABLE, reason="OpenAI package not available")
def test_azure_generator_requires_credentials():
    """Azure generator raises error if credentials missing."""
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


@pytest.mark.skipif(not AZURE_ENV_READY, reason="Azure creds required for strict path")
def test_generate_asset_e2e_validates():
    """Azure strict path yields MCP-validated assets end-to-end."""
    asset = generate_asset(
        "red pulsing shader",
        use_llm=True,
        engine="azure"
    )
    
    # Validate via MCP
    client = MCPClient(schema_version="0.7.3")
    result = client.confirm(asset, strict=True)
    
    assert result["ok"] is True
    assert asset["name"]
