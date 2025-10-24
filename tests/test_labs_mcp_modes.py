"""Tests for MCPClient resolution modes and batch validation."""

from __future__ import annotations

from typing import Any, List

import pytest

from labs.mcp import MCPClient, MCPClientError, MCPValidationError


def _dummy_asset(asset_id: str) -> dict[str, Any]:
    return {
        "$schema": "https://schemas.synesthetic.dev/0.7.3/synesthetic-asset.schema.json",
        "asset_id": asset_id,
        "name": f"Asset {asset_id}",
        "shader": {},
        "tone": {},
        "haptic": {},
        "control": {},
        "modulations": [],
        "rule_bundle": {"rules": [], "meta_info": {}},
        "meta_info": {"provenance": {}},
    }


@pytest.mark.parametrize("resolution", ["preserve", "inline", "bundled"])
def test_mcp_client_fetch_schema_modes(monkeypatch, resolution: str) -> None:
    monkeypatch.delenv("LABS_SCHEMA_VERSION", raising=False)
    client = MCPClient(resolution=resolution)
    descriptor = client.fetch_schema("synesthetic-asset")
    assert descriptor["resolution"] == resolution
    assert descriptor["name"] == "synesthetic-asset"
    assert descriptor["schema_id"]
    assert isinstance(descriptor["schema"], dict)


def test_mcp_client_defaults_to_inline(monkeypatch) -> None:
    monkeypatch.delenv("LABS_SCHEMA_RESOLUTION", raising=False)
    client = MCPClient()
    assert client.resolution == "inline"


def test_mcp_client_fetch_uses_requested_version(monkeypatch) -> None:
    monkeypatch.setenv("LABS_SCHEMA_VERSION", "0.7.3")
    client = MCPClient(resolution="preserve")
    descriptor = client.fetch_schema("synesthetic-asset", version="0.7.3")
    assert descriptor["version"] == "0.7.3"


def test_mcp_client_validate_respects_batch_limit(monkeypatch) -> None:
    client = MCPClient(batch_limit=1)
    assets = [_dummy_asset("one"), _dummy_asset("two")]
    with pytest.raises(MCPClientError) as excinfo:
        client.validate(assets, strict=True)
    assert "batch exceeds limit" in str(excinfo.value)


def test_mcp_client_validate_many_passthrough(monkeypatch) -> None:
    client = MCPClient(batch_limit=3)

    def fake_validate_many(payload: List[dict], *, strict: bool = True) -> List[dict]:
        return [
            {"ok": True, "item": entry.get("asset_id") or entry.get("name")}
            for entry in payload
        ]

    monkeypatch.setattr("mcp.core.validate_many", fake_validate_many)

    assets = [_dummy_asset("alpha"), _dummy_asset("beta")]
    results = client.validate(assets, strict=True)
    items = [item["item"] for item in results]
    assert items == ["alpha", "beta"] or items == ["Asset alpha", "Asset beta"]


def test_mcp_client_confirm_strict_failure(monkeypatch) -> None:
    client = MCPClient()

    def failing_validate_many(payload, *, strict: bool = True):
        return {"ok": False, "items": [{"ok": False, "reason": "broken"}]}

    monkeypatch.setattr("mcp.core.validate_many", failing_validate_many)

    with pytest.raises(MCPValidationError) as excinfo:
        client.confirm(_dummy_asset("bad"), strict=True)

    assert isinstance(excinfo.value.result, dict)
