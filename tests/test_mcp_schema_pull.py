import pytest

from labs.mcp.client import MCPClient
from labs.mcp.exceptions import MCPUnavailableError


@pytest.mark.no_mcp_stub
def test_mcp_fetch_requires_tcp(monkeypatch):
    """TCP fetch failures must bubble up without falling back to local schemas."""

    def failing_fetch(*args, **kwargs):  # pragma: no cover - intentional failure path
        raise MCPUnavailableError("tcp_offline")

    monkeypatch.setattr("labs.mcp.client.get_schema_from_mcp", failing_fetch)

    client = MCPClient(schema_version="0.7.3")

    with pytest.raises(MCPUnavailableError):
        client.fetch_schema("synesthetic-asset", version="0.7.3")
