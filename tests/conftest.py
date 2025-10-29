"""Pytest configuration and MCP fixtures for Synesthetic Labs."""

from __future__ import annotations

import pathlib
import sys
from typing import Dict

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


_SCHEMA_BUNDLE: Dict[str, object] = {
    "$id": "https://schemas.synesthetic-labs.ai/mcp/0.7.3/synesthetic-asset.schema.json",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {"type": "string"},
        "meta_info": {"type": "object"},
        "shader": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "vertex_shader": {"type": "string"},
                "fragment_shader": {"type": "string"},
                "description": {"type": "string"},
                "meta_info": {"type": "object"},
                "uniforms": {"type": "array"},
            },
            "required": ["fragment_shader"],
        },
        "tone": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "synth": {"type": "object"},
                "patterns": {"type": "array"},
                "parts": {"type": "array"},
                "effects": {"type": "array"},
                "meta_info": {"type": "object"},
                "description": {"type": "string"},
                "input_parameters": {"type": "array"},
            },
        },
        "haptic": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "device": {"type": "object"},
                "input_parameters": {"type": "array"},
                "description": {"type": "string"},
                "meta_info": {"type": "object"},
            },
        },
        "control": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "control_parameters": {"type": "array"},
                "meta_info": {"type": "object"},
                "description": {"type": "string"},
            },
        },
        "modulations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "target": {"type": "string"},
                    "type": {"type": "string"},
                    "waveform": {"type": "string"},
                    "frequency": {"type": "number"},
                    "amplitude": {"type": "number"},
                    "offset": {"type": "number"},
                    "phase": {"type": "number"},
                    "scale": {"type": "number"},
                    "scaleProfile": {"type": "string"},
                    "min": {"type": "number"},
                    "max": {"type": "number"},
                },
            },
        },
        "rule_bundle": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "rules": {"type": "array"},
                "meta_info": {"type": "object"},
            },
        },
    },
}


@pytest.fixture(autouse=True)
def _stub_mcp_transport(monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest) -> None:
    """Provide deterministic TCP stubs for MCP interactions in tests."""

    if request.node.get_closest_marker("requires_real_tcp") or request.node.get_closest_marker("no_mcp_stub"):
        return

    descriptor = {
        "ok": True,
        "name": "synesthetic-asset",
        "version": "0.7.3",
        "resolution": "inline",
        "schema": _SCHEMA_BUNDLE,
        "schema_id": _SCHEMA_BUNDLE["$id"],
    }

    def fake_get_schema_from_mcp(name: str, *, version: str | None = None, resolution: str | None = None, **_: object):
        return descriptor

    class DummyValidator:
        def __init__(self, host: str, port: int, *, timeout: float = 10.0) -> None:
            self.host = host
            self.port = port
            self.timeout = timeout

        def validate(self, asset: Dict[str, object]) -> Dict[str, object]:
            schema_uri = asset.get("$schema")
            if not isinstance(schema_uri, str) or not schema_uri:
                return {
                    "ok": False,
                    "reason": "missing_schema",
                    "errors": [{"message": "$schema is required"}],
                }

            name = asset.get("name")
            if not name:
                return {
                    "ok": False,
                    "reason": "validation_failed",
                    "errors": [{"message": "name is required"}],
                }
            return {"ok": True, "reason": "validation_passed", "errors": []}

    monkeypatch.setenv("MCP_HOST", "127.0.0.1")
    monkeypatch.setenv("MCP_PORT", "8765")
    monkeypatch.setattr("labs.mcp.tcp_client.get_schema_from_mcp", fake_get_schema_from_mcp)
    monkeypatch.setattr("labs.mcp.client.get_schema_from_mcp", fake_get_schema_from_mcp)
    monkeypatch.setattr("labs.mcp.tcp_client.TcpMCPValidator", DummyValidator)
    monkeypatch.setattr("labs.mcp.client.TcpMCPValidator", DummyValidator)
