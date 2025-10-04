"""MCP resolver and validation tests."""

from __future__ import annotations

from labs.generator import AssetAssembler
from labs.mcp.validate import validate_asset, validate_many
from labs.mcp_stdio import resolve_mcp_endpoint


def test_resolve_mcp_endpoint_invalid_falls_back_to_tcp(monkeypatch) -> None:
    monkeypatch.setenv("MCP_ENDPOINT", "unsupported-protocol")

    endpoint = resolve_mcp_endpoint()

    assert endpoint == "tcp"


def test_validate_asset_requires_top_level_schema() -> None:
    result = validate_asset({})

    assert result["ok"] is False
    assert result["reason"] == "validation_failed"
    assert result["errors"][0]["path"] == "/$schema"


def test_validate_asset_rejects_schema_ref() -> None:
    result = validate_asset({"$schemaRef": "meta/schemas/synesthetic-asset.schema.json"})

    assert result["ok"] is False
    assert result["reason"] == "validation_failed"
    assert "$schemaRef" in result["errors"][0]["msg"]


def test_validate_asset_accepts_generated_asset() -> None:
    assembler = AssetAssembler()
    asset = assembler.generate("validator smoke test", schema_version="0.7.4")

    result = validate_asset(asset)

    assert result == {"ok": True, "reason": "validation_passed", "errors": []}


def test_validate_many_rolls_up_failures() -> None:
    assembler = AssetAssembler()
    asset = assembler.generate("batch validation", schema_version="0.7.4")

    batch = [asset, {"$schema": "meta/schemas/synesthetic-asset.schema.json", "asset_id": 1}]

    response = validate_many(batch)

    assert response["ok"] is False
    assert response["reason"] == "validation_failed"
    assert len(response["items"]) == 2
    assert response["items"][0]["ok"] is True
    assert response["items"][1]["ok"] is False
