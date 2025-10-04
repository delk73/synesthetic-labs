"""Local MCP validator helpers aligned with the v0.2.8 spec."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, MutableMapping

import jsonschema
from jsonschema import Draft202012Validator, ValidationError

JsonDict = Dict[str, Any]

_ROOT = Path(__file__).resolve().parent.parent.parent
_VALIDATOR_CACHE: Dict[str, Draft202012Validator] = {}


def _resolve_schema_path(schema_identifier: str) -> Path:
    if not isinstance(schema_identifier, str) or not schema_identifier.strip():
        raise ValueError("schema identifier must be a non-empty string")

    identifier = schema_identifier.strip()
    if identifier.startswith("http://") or identifier.startswith("https://"):
        raise ValueError(f"remote schemas are not supported: {identifier}")

    path = Path(identifier)
    if not path.is_absolute():
        path = (_ROOT / path).resolve()
    return path


def _load_validator(schema_identifier: str) -> Draft202012Validator:
    if schema_identifier not in _VALIDATOR_CACHE:
        schema_path = _resolve_schema_path(schema_identifier)
        with schema_path.open("r", encoding="utf-8") as handle:
            schema_payload = json.load(handle)
        _VALIDATOR_CACHE[schema_identifier] = Draft202012Validator(schema_payload)
    return _VALIDATOR_CACHE[schema_identifier]


def _format_error(error: ValidationError) -> JsonDict:
    tokens = [str(token) for token in error.path]
    pointer = "/" + "/".join(tokens) if tokens else "/"
    return {"path": pointer, "msg": error.message}


def _failure(reason: str, errors: List[JsonDict]) -> JsonDict:
    return {"ok": False, "reason": reason, "errors": errors}


def validate_asset(asset: MutableMapping[str, Any], *_) -> JsonDict:
    if not isinstance(asset, MutableMapping):
        raise TypeError("asset must be a mutable mapping")

    if "$schemaRef" in asset:
        return _failure(
            "validation_failed",
            [
                {
                    "path": "/$schema",
                    "msg": "$schemaRef is no longer supported (use $schema)",
                }
            ],
        )

    schema_identifier = asset.get("$schema")
    if not isinstance(schema_identifier, str) or not schema_identifier.strip():
        return _failure(
            "validation_failed",
            [
                {
                    "path": "/$schema",
                    "msg": "top-level $schema is required",
                }
            ],
        )

    try:
        validator = _load_validator(schema_identifier)
    except (OSError, ValueError) as exc:
        return _failure(
            "validation_failed",
            [
                {
                    "path": "/$schema",
                    "msg": f"schema_unavailable: {exc}",
                }
            ],
        )

    try:
        validator.validate(dict(asset))
    except ValidationError as exc:
        return _failure("validation_failed", [_format_error(exc)])

    return {"ok": True, "reason": "validation_passed", "errors": []}


def validate_many(assets: Iterable[MutableMapping[str, Any]], *_) -> JsonDict:
    results: List[JsonDict] = []
    for asset in assets:
        results.append(validate_asset(asset))

    ok = all(entry["ok"] for entry in results)
    payload: JsonDict = {"ok": ok, "items": results}
    if not ok:
        payload["reason"] = "validation_failed"
    else:
        payload["reason"] = "validation_passed"
    return payload


__all__ = ["validate_asset", "validate_many"]
