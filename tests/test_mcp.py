"""MCP resolver tests."""

from __future__ import annotations

from labs.mcp_stdio import resolve_mcp_endpoint


def test_resolve_mcp_endpoint_invalid_falls_back_to_tcp(monkeypatch) -> None:
    monkeypatch.setenv("MCP_ENDPOINT", "unsupported-protocol")

    endpoint = resolve_mcp_endpoint()

    assert endpoint == "tcp"
