"""Schema-driven builder integration tests for version 0.7.3."""

from labs.mcp.client import MCPClient
from labs.v0_7_3.generator import generate_asset


def test_all_components_validate():
    """Minimally generated asset validates against strict MCP schema."""
    client = MCPClient(schema_version="0.7.3")
    asset = generate_asset("schema-driven test", use_llm=False)
    result = client.confirm(asset, strict=True)
    assert result["ok"], result
