"""Global pytest configuration enforcing live MCP dependencies."""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

from labs.mcp.client import MCPClient, MCPClientError
from labs.mcp.exceptions import MCPUnavailableError


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers used throughout the suite."""

    config.addinivalue_line(
        "markers",
        "requires_real_tcp: mark test as exercising real TCP sockets",
    )
    config.addinivalue_line(
        "markers",
        "requires_mcp: mark test as requiring a live MCP endpoint",
    )


@pytest.fixture(scope="session", autouse=True)
def _require_live_mcp() -> None:
    """Fail the suite early when the MCP TCP endpoint is unavailable."""

    client = MCPClient()
    try:
        descriptor = client.fetch_schema(client.schema_name, version=client.schema_version)
    except (MCPUnavailableError, MCPClientError) as exc:
        pytest.fail(f"MCP inline schema unavailable via TCP: {exc}")

    schema = descriptor.get("schema")
    if not isinstance(schema, dict):
        pytest.fail("MCP schema response missing inline bundle")
