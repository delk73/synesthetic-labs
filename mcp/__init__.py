"""Local MCP core compatibility layer for schema discovery."""

from __future__ import annotations

from .core import get_schema, list_schemas, validate_many

__all__ = ["get_schema", "list_schemas", "validate_many"]
