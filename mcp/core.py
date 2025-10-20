"""Minimal MCP core emulation for local CI and development.

This module exposes helpers that mirror the upstream ``mcp.core`` package used
by Synesthetic Labs.  The local implementation focuses on deterministic
filesystem discovery so that tests can run without requiring the full backend
repository.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

JsonDict = Dict[str, object]

_SEMVER_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
_SCHEMA_SUFFIX = ".schema.json"
_VALID_RESOLUTIONS = {"preserve", "inline", "bundled"}


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _default_schema_root() -> Path:
    return _repo_root() / "meta" / "schemas"


def _iter_schema_roots() -> Iterator[Path]:
    """Yield schema directories in priority order."""

    seen: set[Path] = set()
    env_value = os.getenv("SYN_SCHEMAS_DIR", "").strip()
    if env_value:
        for chunk in env_value.split(os.pathsep):
            if not chunk:
                continue
            path = Path(chunk).expanduser()
            try:
                resolved = path.resolve(strict=False)
            except OSError:
                # Fall back to the unresolved path if resolution fails.
                resolved = path
            if resolved in seen:
                continue
            seen.add(resolved)
            if resolved.exists() and resolved.is_dir():
                yield resolved

    candidates: List[Path] = []
    candidates.append(_default_schema_root())

    repo_root = _repo_root()
    repo_parent = repo_root.parent
    additional_roots = [
        repo_parent / "synesthetic-mcp" / "libs" / "synesthetic-schemas" / "docs" / "schema",
        repo_parent / "synesthetic-mcp" / "libs" / "synesthetic-schemas" / "jsonschema",
        repo_parent / "synesthetic-schemas" / "docs" / "schema",
        repo_parent / "synesthetic-schemas" / "jsonschema",
    ]
    for candidate in additional_roots:
        candidates.append(candidate)

    for candidate in candidates:
        try:
            resolved = candidate.resolve(strict=True)
        except OSError:
            resolved = candidate
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.exists() and resolved.is_dir():
            yield resolved


def _version_key(version: Optional[str]) -> Tuple[int, int, int, int]:
    if not version or not _SEMVER_PATTERN.match(version):
        # Treat unknown versions as the lowest possible priority.
        return (-1, -1, -1, 0)
    major, minor, patch = (int(part) for part in version.split("."))
    # Positive values ensure they sort after the unknown entries.
    return (major, minor, patch, 1)


def _iter_schema_files(root: Path) -> Iterator[Tuple[Path, Optional[str]]]:
    if not root.exists():
        return
    try:
        entries = list(root.iterdir())
    except OSError:
        return
    for entry in entries:
        if entry.is_dir() and _SEMVER_PATTERN.match(entry.name):
            try:
                for child in entry.glob(f"*{_SCHEMA_SUFFIX}"):
                    if child.is_file():
                        yield child, entry.name
            except OSError:
                continue
        elif entry.is_file() and entry.name.endswith(_SCHEMA_SUFFIX):
            yield entry, None


def _load_schema(path: Path) -> JsonDict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _build_response(
    *,
    name: str,
    version: Optional[str],
    source: Path,
    schema: Optional[JsonDict] = None,
    ok: bool = True,
    reason: Optional[str] = None,
) -> JsonDict:
    payload: JsonDict = {
        "ok": ok,
        "name": name,
        "path": str(source),
        "version": version or "unknown",
    }
    if schema is not None:
        payload["schema"] = schema
    if reason:
        payload["reason"] = reason
    return payload


def _catalog_schemas() -> Dict[str, List[Tuple[Optional[str], Path]]]:
    catalog: Dict[str, List[Tuple[Optional[str], Path]]] = {}
    for root in _iter_schema_roots():
        for schema_path, version in _iter_schema_files(root):
            name = schema_path.name[:-len(_SCHEMA_SUFFIX)]
            catalog.setdefault(name, []).append((version, schema_path))
    for versions in catalog.values():
        versions.sort(key=lambda item: _version_key(item[0]))
    return catalog


def list_schemas() -> JsonDict:
    """Return a summary of all discoverable schemas."""

    catalog = _catalog_schemas()
    if not catalog:
        return {"ok": False, "reason": "schema_directory_unavailable"}

    summary: Dict[str, JsonDict] = {}
    for name, versions in catalog.items():
        entries: List[JsonDict] = []
        for version, path in versions:
            entries.append({
                "version": version or "unknown",
                "path": str(path),
            })
        summary[name] = {
            "name": name,
            "versions": entries,
            "latest": entries[-1]["version"],
        }

    return {"ok": True, "schemas": summary}


def _normalise_resolution(resolution: Optional[str]) -> str:
    if resolution is None:
        return "preserve"
    candidate = resolution.strip().lower()
    if candidate not in _VALID_RESOLUTIONS:
        raise ValueError(f"unsupported schema resolution: {resolution}")
    return candidate


def get_schema(
    name: str,
    version: Optional[str] = None,
    *,
    resolution: Optional[str] = None,
) -> JsonDict:
    """Load a schema by *name*, preferring the highest available version."""

    _normalise_resolution(resolution)

    if not isinstance(name, str) or not name.strip():
        raise ValueError("schema name must be a non-empty string")

    normalized = name.strip()
    catalog = _catalog_schemas()

    candidates = catalog.get(normalized, [])
    fallback_requested = False

    if version:
        filtered = [item for item in candidates if item[0] == version]
        if filtered:
            candidates = filtered
        else:
            fallback_requested = True
            if not candidates:
                # Fallback to direct filesystem check in case the cache missed it
                for root in _iter_schema_roots():
                    candidate_path = root / version / f"{normalized}{_SCHEMA_SUFFIX}"
                    if candidate_path.exists():
                        schema_data = _load_schema(candidate_path)
                        response = _build_response(
                            name=normalized,
                            version=version,
                            source=candidate_path,
                            schema=schema_data,
                        )
                        response["requested_version"] = version
                        return response
                return _build_response(
                    name=normalized,
                    version=version,
                    source=Path(version),
                    ok=False,
                    reason=f"schema_not_found:{normalized}:{version}",
                )

    if not candidates:
        return _build_response(
            name=normalized,
            version=version,
            source=Path(normalized),
            ok=False,
            reason=f"schema_not_found:{normalized}",
        )

    # Choose the last entry because the catalog is sorted in ascending order.
    selected_version, selected_path = candidates[-1]
    try:
        schema_payload = _load_schema(selected_path)
    except OSError as exc:
        return _build_response(
            name=normalized,
            version=selected_version,
            source=selected_path,
            ok=False,
            reason=f"schema_load_failed:{exc}",
        )

    payload = _build_response(
        name=normalized,
        version=selected_version,
        source=selected_path,
        schema=schema_payload,
    )
    if fallback_requested and version and selected_version != version:
        payload["requested_version"] = version
    return payload


def validate_many(assets, *, strict: bool = True):
    """Validate a batch of assets via the local schema catalogue.

    The upstream MCP package exposes ``validate_many`` with transport-backed
    behaviour.  For the local compatibility layer we defer to the in-repo
    validator so that the call signature matches tests without depending on the
    external adapter binary.
    """

    from typing import Iterable, MutableMapping  # local import to avoid cycle

    if not isinstance(assets, Iterable):
        raise TypeError("assets must be an iterable of mappings")

    results = []
    ok = True

    try:
        from labs.mcp.validate import validate_asset  # noqa: WPS433 - intentional local import
    except ImportError as exc:  # pragma: no cover - defensive: labs module missing
        raise RuntimeError("labs.mcp.validate unavailable") from exc

    for candidate in assets:
        if not isinstance(candidate, MutableMapping):
            raise TypeError("each asset must be a mutable mapping")
        result = validate_asset(candidate)
        ok = ok and bool(result.get("ok"))
        results.append(result)

    payload: JsonDict = {"ok": ok, "items": results}
    payload["reason"] = "validation_passed" if ok else "validation_failed"
    if strict and not ok:
        payload["strict"] = True
    return payload


__all__ = ["get_schema", "list_schemas", "validate_many"]
