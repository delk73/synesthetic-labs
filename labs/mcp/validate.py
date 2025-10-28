"""Local JSON Schema validation helpers for MCP compatibility."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping
from urllib.parse import urlparse

from jsonschema import Draft202012Validator, ValidationError
from referencing import Registry, Resource, exceptions

from labs.mcp.client import MCPClientError, load_schema_bundle

_VERSION_PATTERN = re.compile(r"/(\d+\.\d+\.\d+)/")


def validate_asset(candidate: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate a synesthetic asset against its declared schema."""

    if not isinstance(candidate, Mapping):
        raise TypeError("candidate asset must be a mapping")

    schema_uri = candidate.get("$schema")
    if not isinstance(schema_uri, str) or not schema_uri.strip():
        return {
            "ok": False,
            "reason": "missing_schema",
            "errors": [{"message": "$schema field missing", "path": []}],
        }

    version = _extract_version(schema_uri) or "0.7.3"
    try:
        schema = load_schema_bundle(version=version)
    except MCPClientError as exc:
        return {
            "ok": False,
            "reason": "schema_load_failed",
            "errors": [{"message": str(exc), "path": []}],
        }

    registry = _build_registry(version, schema)
    validator = Draft202012Validator(schema, registry=registry)
    payload = dict(candidate)
    payload.pop("$schema", None)
    errors = list(_collect_errors(validator.iter_errors(payload)))
    if errors:
        return {"ok": False, "reason": "validation_failed", "errors": errors}
    return {"ok": True, "reason": "validation_passed", "errors": []}


def _collect_errors(raw_errors: Iterable[ValidationError]):
    for error in raw_errors:
        path = list(error.absolute_path)
        yield {
            "message": error.message,
            "path": path,
        }


def _extract_version(schema_uri: Any) -> str | None:
    if not isinstance(schema_uri, str):
        return None
    match = _VERSION_PATTERN.search(schema_uri)
    if match:
        return match.group(1)
    return None


def _build_registry(version: str, root_schema: Mapping[str, Any]) -> Registry:
    """Create a referencing registry that resolves Synesthetic schema URIs."""

    def _retrieve(uri: str):
        parsed = urlparse(uri)
        path = parsed.path or ""
        if not path.endswith(".schema.json"):
            raise exceptions.NoSuchResource(uri=uri)
        schema_name = Path(path).name[:-len(".schema.json")]
        try:
            bundle = load_schema_bundle(schema_name=schema_name, version=version)
        except MCPClientError as exc:
            raise exceptions.NoSuchResource(uri=uri) from exc
        return Resource.from_contents(bundle)

    registry = Registry(retrieve=_retrieve)
    schema_id = root_schema.get("$id")
    if isinstance(schema_id, str) and schema_id:
        registry = registry.with_resources({schema_id: Resource.from_contents(root_schema)}.items())
    return registry


__all__ = ["validate_asset"]
