"""
Telemetry layer for schema version 0.7.3.
Wraps validated assets with operational metadata.
NEVER mixes telemetry with MCP validation contract.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from labs.logging import log_jsonl


def create_telemetry_record(
    asset: Dict[str, Any],
    validation_result: Dict[str, Any],
    *,
    engine: Optional[str] = None,
    deployment: Optional[str] = None,
    prompt: Optional[str] = None,
    **extra_fields
) -> Dict[str, Any]:
    """
    Wrap validated asset with telemetry metadata.
    
    Args:
        asset: MCP-validated asset structure (pure, no telemetry)
        validation_result: Result from client.confirm()
        engine: LLM engine used ("azure", "gemini", etc.)
        deployment: Model deployment name
        prompt: User prompt
        **extra_fields: Additional metadata fields
        
    Returns:
        Telemetry record for logging (asset + metadata)
    """
    record = {
        "trace_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "schema_version": _extract_version_from_asset(asset),
        "asset": asset,  # Pure validated structure
        "validation_result": validation_result,
    }
    
    # Optional fields
    if engine:
        record["engine"] = engine
    if deployment:
        record["deployment"] = deployment
    if prompt:
        record["prompt"] = prompt
    
    # Merge extra fields
    record.update(extra_fields)
    
    return record


def log_generation(
    asset: Dict[str, Any],
    validation_result: Dict[str, Any],
    *,
    log_path: str = "meta/output/labs/v0_7_3_generation.jsonl",
    **metadata
) -> None:
    """
    Log generation event with telemetry.
    
    Args:
        asset: Validated asset
        validation_result: MCP validation result
        log_path: Path to telemetry log file
        **metadata: Additional metadata (engine, deployment, prompt, etc.)
    """
    record = create_telemetry_record(
        asset=asset,
        validation_result=validation_result,
        **metadata
    )
    
    log_jsonl(log_path, record)


def _extract_version_from_asset(asset: Dict[str, Any]) -> Optional[str]:
    """Extract schema version from asset $schema field."""
    schema_field = asset.get("$schema")
    if isinstance(schema_field, str) and schema_field.strip():
        # Extract version from URL like: .../0.7.3/synesthetic-asset.schema.json
        tokens = schema_field.rstrip("/").split("/")
        if tokens:
            candidate = tokens[-2] if len(tokens) >= 2 else tokens[-1]
            # Check if it looks like a version (digits and dots)
            if candidate and all(ch.isdigit() or ch == "." for ch in candidate):
                return candidate
    return None


__all__ = ["create_telemetry_record", "log_generation"]
