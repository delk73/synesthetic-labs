"""
Validation tests for schema version 0.7.3.
These tests define the contract - written FIRST (TDD).
"""

import pytest
from labs.mcp.client import MCPClient, MCPValidationError


def test_minimal_valid_asset_passes_mcp():
    """
    Most basic asset that satisfies schema requirements.
    This test defines what we're building toward.
    
    We don't know the exact schema structure yet - this test will tell us
    by failing with validation errors that show what's required.
    """
    # Start with a minimal guess at the structure
    asset = {
        "$schema": "https://delk73.github.io/synesthetic-schemas/schema/0.7.3/synesthetic-asset.schema.json",
        "name": "minimal_test",
        "meta_info": {}
    }
    
    client = MCPClient(schema_version="0.7.3")
    result = client.confirm(asset, strict=True)
    
    # Assert validation passes
    assert result["ok"] is True


def test_invalid_asset_fails_mcp():
    """Ensure validation actually rejects bad assets."""
    asset = {"name": "incomplete"}  # Missing required fields
    
    client = MCPClient(schema_version="0.7.3")
    
    # Should raise MCPValidationError
    with pytest.raises(MCPValidationError):
        client.confirm(asset, strict=True)


def test_mcp_client_fetches_schema():
    """Verify MCP serves 0.7.3 schema."""
    client = MCPClient(schema_version="0.7.3")
    descriptor = client.fetch_schema("synesthetic-asset", version="0.7.3")
    
    assert descriptor["ok"] is True
    assert descriptor["version"] == "0.7.3"
    assert "schema" in descriptor
    assert descriptor["resolution"] == "inline"


def test_schema_bundle_loads():
    """Verify we can load the schema bundle."""
    from labs.mcp.client import load_schema_bundle
    
    bundle = load_schema_bundle(version="0.7.3")
    
    assert "$schema" in bundle or "type" in bundle
    assert bundle.get("type") == "object"
    assert "properties" in bundle
    assert "name" in bundle["properties"]
