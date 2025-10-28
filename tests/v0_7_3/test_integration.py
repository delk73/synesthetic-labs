"""
Integration tests for schema version 0.7.3.
Tests complete end-to-end flow: generate → validate → telemetry.
"""

import json
from pathlib import Path
import pytest
from labs.v0_7_3 import generate_asset, log_generation
from labs.mcp.client import MCPClient, load_schema_bundle


def test_complete_generation_flow():
    """
    End-to-end test: generate → validate → telemetry.
    This is the core workflow for any schema version.
    """
    # Step 1: Generate asset
    asset = generate_asset("test shader", use_llm=False)
    
    # Step 2: Validate via MCP
    client = MCPClient(schema_version="0.7.3")
    result = client.confirm(asset, strict=True)
    
    # Step 3: Verify validation passed
    assert result["ok"] is True
    
    # Step 4: Verify asset structure
    assert "$schema" in asset
    assert "0.7.3" in asset["$schema"]
    assert asset["name"] == "test_shader"
    
    # Step 5: Verify asset is pure (no telemetry)
    assert "trace_id" not in asset
    assert "engine" not in asset


def test_schema_fetch_and_inline_resolution():
    """Verify schema fetch returns inline-resolved bundle."""
    client = MCPClient(schema_version="0.7.3")
    descriptor = client.fetch_schema("synesthetic-asset", version="0.7.3")
    
    # Verify descriptor structure
    assert descriptor["ok"] is True
    assert descriptor["version"] == "0.7.3"
    assert descriptor["resolution"] == "inline"
    assert "schema" in descriptor
    
    # Verify schema bundle
    schema = descriptor["schema"]
    assert isinstance(schema, dict)
    assert "type" in schema
    assert schema["type"] == "object"
    assert "properties" in schema
    assert "name" in schema["properties"]


def test_load_schema_bundle_convenience():
    """Verify load_schema_bundle() convenience function."""
    bundle = load_schema_bundle(version="0.7.3")
    
    # Verify bundle structure
    assert isinstance(bundle, dict)
    assert bundle.get("type") == "object"
    assert "properties" in bundle
    assert "required" in bundle
    
    # Verify key properties exist
    props = bundle["properties"]
    assert "name" in props
    assert "meta_info" in props


def test_batch_validation():
    """Verify batch validation of multiple assets."""
    # Generate multiple assets
    assets = [
        generate_asset(f"test_{i}", use_llm=False)
        for i in range(3)
    ]
    
    # Batch validate
    client = MCPClient(schema_version="0.7.3")
    results = client.validate(assets, strict=True)
    
    # All should pass
    assert len(results) == 3
    assert all(r["ok"] for r in results)


def test_telemetry_logging_e2e(tmp_path):
    """End-to-end test of telemetry logging."""
    log_file = tmp_path / "integration.jsonl"
    
    # Generate and validate
    asset = generate_asset("integration test", use_llm=False)
    client = MCPClient(schema_version="0.7.3")
    result = client.confirm(asset, strict=True)
    
    # Log with telemetry
    log_generation(
        asset=asset,
        validation_result=result,
        log_path=str(log_file),
        engine="integration_test",
        prompt="integration test"
    )
    
    # Verify log file
    assert log_file.exists()
    
    # Parse log
    record = json.loads(log_file.read_text().strip())
    
    # Verify telemetry structure
    assert record["trace_id"]
    assert record["timestamp"]
    assert record["schema_version"] == "0.7.3"
    assert record["engine"] == "integration_test"
    assert record["prompt"] == "integration test"
    assert record["validation_result"]["ok"] is True
    
    # Verify asset in record is unchanged
    assert record["asset"] == asset
    assert "trace_id" not in record["asset"]


def test_strict_validation_fails_on_invalid():
    """Verify strict validation raises on invalid assets."""
    # Invalid asset (missing required field)
    invalid_asset = {
        "$schema": "https://delk73.github.io/synesthetic-schemas/schema/0.7.3/synesthetic-asset.schema.json",
        # Missing "name" (required)
        "meta_info": {}
    }
    
    client = MCPClient(schema_version="0.7.3")
    
    from labs.mcp.client import MCPValidationError
    with pytest.raises(MCPValidationError):
        client.confirm(invalid_asset, strict=True)


def test_version_namespace_isolation():
    """Verify v0_7_3 namespace is isolated."""
    # Import v0_7_3 module
    import labs.v0_7_3
    
    # Verify expected exports
    assert hasattr(labs.v0_7_3, "generate_asset")
    assert hasattr(labs.v0_7_3, "create_telemetry_record")
    assert hasattr(labs.v0_7_3, "log_generation")
    
    # Verify callable
    assert callable(labs.v0_7_3.generate_asset)


def test_mcp_client_forces_inline():
    """Verify MCPClient forces inline resolution."""
    # Try to request different resolution modes
    for mode in ["preserve", "bundled", "inline"]:
        client = MCPClient(schema_version="0.7.3", resolution=mode)
        
        # Should always be forced to inline
        assert client.resolution == "inline"
        
        # Fetch should return inline
        descriptor = client.fetch_schema("synesthetic-asset", version="0.7.3")
        assert descriptor["resolution"] == "inline"
