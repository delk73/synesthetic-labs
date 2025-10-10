"""Local MCP validator helpers aligned with the v0.2.8 spec."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, MutableMapping

import jsonschema
from jsonschema import Draft202012Validator, ValidationError
from urllib.parse import urlparse

JsonDict = Dict[str, Any]

_ROOT = Path(__file__).resolve().parent.parent.parent
_VALIDATOR_CACHE: Dict[str, Draft202012Validator] = {}


def _resolve_schema_path(schema_identifier: str) -> Path:
    if not isinstance(schema_identifier, str) or not schema_identifier.strip():
        raise ValueError("schema identifier must be a non-empty string")

    identifier = schema_identifier.strip()
    parsed = urlparse(identifier)
    if parsed.scheme in {"http", "https"}:
        path_segments = [part for part in Path(parsed.path).parts if part]
        if not path_segments:
            raise ValueError(f"unsupported remote schema: {identifier}")

        filename = Path(path_segments[-1]).name
        if not filename or re.fullmatch(r"\d+\.\d+\.\d+", filename):
            raise ValueError(f"schema filename required: {identifier}")

        candidates = []
        version_match = re.search(r"(\d+\.\d+\.\d+)", parsed.path)
        if version_match:
            version = version_match.group(1)
            candidates.append(Path("meta") / "schemas" / version / filename)

        candidates.append(Path("meta") / "schemas" / filename)
        root = _ROOT.resolve()
        for candidate in candidates:
            candidate_path = (root / candidate).resolve()
            if candidate_path.exists():
                return candidate_path
        raise ValueError(f"schema_not_found:{identifier}")

    path = Path(identifier)
    if not path.name or re.fullmatch(r"\d+\.\d+\.\d+", path.name):
        raise ValueError(f"schema filename required: {identifier}")

    if not path.is_absolute():
        path = (_ROOT / path).resolve()
    else:
        path = path.resolve()
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


def invoke_mcp(asset: MutableMapping[str, Any], strict: bool = True) -> JsonDict:
    """Validate *asset* via MCP, raising on strict-mode failures."""

    result = validate_asset(asset)
    if strict and not result.get("ok"):
        error = ValidationError("strict validation failed")
        setattr(error, "result", result)
        raise error
    if not strict and not result.get("ok"):
        print("[WARN] relaxed validation: asset persisted with warnings")
    return result


__all__ = ["validate_asset", "validate_many", "invoke_mcp"]
