"""
Telemetry tests for schema version 0.7.3.
Ensures telemetry stays separate from validation contract.
"""

import json
from pathlib import Path
import pytest
from labs.v0_7_3.telemetry import create_telemetry_record, log_generation
from labs.v0_7_3.generator import generate_asset
from labs.mcp.client import MCPClient


def test_telemetry_record_wraps_asset():
    """Telemetry record wraps validated asset without modifying it."""
    asset = {
        "$schema": "https://delk73.github.io/synesthetic-schemas/schema/0.7.3/synesthetic-asset.schema.json",
        "name": "test",
        "meta_info": {}
    }
    
    validation_result = {"ok": True}
    
    record = create_telemetry_record(
        asset=asset,
        validation_result=validation_result,
        engine="azure",
        deployment="gpt-4o-mini",
        prompt="test prompt"
    )
    
    # Check telemetry fields
    assert "trace_id" in record
    assert "timestamp" in record
    assert "schema_version" in record
    assert record["schema_version"] == "0.7.3"
    assert record["engine"] == "azure"
    assert record["deployment"] == "gpt-4o-mini"
    assert record["prompt"] == "test prompt"
    
    # Check asset is wrapped (not modified)
    assert record["asset"] == asset
    assert record["validation_result"] == validation_result
    
    # Original asset unchanged
    assert "trace_id" not in asset
    assert "engine" not in asset


def test_telemetry_separates_concerns():
    """Telemetry metadata stays separate from validated asset."""
    # Generate and validate asset
    asset = generate_asset("test", use_llm=False)
    client = MCPClient(schema_version="0.7.3")
    result = client.confirm(asset, strict=True)
    
    # Asset should be pure (no telemetry)
    assert "trace_id" not in asset
    assert "engine" not in asset
    assert "deployment" not in asset
    assert "timestamp" not in asset
    
    # Telemetry wraps it
    record = create_telemetry_record(
        asset=asset,
        validation_result=result,
        engine="test_engine"
    )
    
    # Record has telemetry
    assert "trace_id" in record
    assert record["engine"] == "test_engine"
    
    # But asset inside record is still pure
    assert "trace_id" not in record["asset"]
    assert "engine" not in record["asset"]


def test_log_generation_writes_jsonl(tmp_path):
    """log_generation writes structured JSONL."""
    log_file = tmp_path / "test_generation.jsonl"
    
    asset = generate_asset("test", use_llm=False)
    client = MCPClient(schema_version="0.7.3")
    result = client.confirm(asset, strict=True)
    
    # Log it
    log_generation(
        asset=asset,
        validation_result=result,
        log_path=str(log_file),
        engine="test",
        prompt="test prompt"
    )
    
    # Verify file exists and is valid JSON
    assert log_file.exists()
    
    content = log_file.read_text()
    record = json.loads(content.strip())
    
    # Check structure
    assert record["asset"] == asset
    assert record["validation_result"] == result
    assert record["engine"] == "test"
    assert record["prompt"] == "test prompt"
    assert "trace_id" in record
    assert "timestamp" in record


def test_telemetry_extracts_version():
    """Telemetry extracts schema version from $schema field."""
    asset = {
        "$schema": "https://delk73.github.io/synesthetic-schemas/schema/0.7.3/synesthetic-asset.schema.json",
        "name": "test"
    }
    
    record = create_telemetry_record(
        asset=asset,
        validation_result={"ok": True}
    )
    
    assert record["schema_version"] == "0.7.3"


def test_telemetry_optional_fields():
    """Telemetry fields are optional."""
    asset = {"$schema": "...", "name": "test"}
    
    # Minimal record (no optional fields)
    record = create_telemetry_record(
        asset=asset,
        validation_result={"ok": True}
    )
    
    # Required fields present
    assert "trace_id" in record
    assert "timestamp" in record
    assert "asset" in record
    assert "validation_result" in record
    
    # Optional fields absent
    assert "engine" not in record
    assert "deployment" not in record
    assert "prompt" not in record


def test_telemetry_extra_fields():
    """Telemetry accepts arbitrary extra fields."""
    asset = {"$schema": "...", "name": "test"}
    
    record = create_telemetry_record(
        asset=asset,
        validation_result={"ok": True},
        custom_field="custom_value",
        another_field=123
    )
    
    assert record["custom_field"] == "custom_value"
    assert record["another_field"] == 123
