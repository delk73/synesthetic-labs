import os
import sys

def test_mcp_schema_pull(monkeypatch):
    """
    Verify that Labs can import MCP and pull schemas via core.get_schema.
    """

    # Point at backend schemas
    monkeypatch.setenv("SYN_SCHEMAS_DIR", "/home/dce/src/sdfk-backend/meta/schemas")

    # Ensure backend repo is importable
    if "/home/dce/src/sdfk-backend" not in sys.path:
        sys.path.insert(0, "/home/dce/src/sdfk-backend")

    from mcp.core import get_schema, list_schemas

    result = list_schemas()
    assert result["ok"], f"list_schemas failed: {result}"

    schema = get_schema("synesthetic-asset")
    assert schema["ok"], f"get_schema failed: {schema}"

    print("Schema version:", schema["version"])
    print("Schema $id:", schema["schema"].get("$id"))

    # Basic structural checks
    s = schema["schema"]
    assert "properties" in s, "Schema missing 'properties'"
    assert "shader" in s["properties"], "Schema missing 'shader' property"
