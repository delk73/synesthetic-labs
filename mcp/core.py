"""Minimal MCP core emulation for local CI and development.

This module exposes the ``get_schema`` and ``list_schemas`` helpers that the
Synesthetic Labs tooling expects from the upstream ``mcp.core`` package.  The
implementation intentionally focuses on deterministic filesystem discovery so
that tests can run without requiring the full backend repository.
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

    default_root = _default_schema_root()
    try:
        default_resolved = default_root.resolve(strict=True)
    except OSError:
        default_resolved = default_root
    if default_resolved not in seen and default_resolved.exists():
        yield default_resolved


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


def get_schema(name: str, version: Optional[str] = None) -> JsonDict:
    """Load a schema by *name*, preferring the highest available version."""

    if not isinstance(name, str) or not name.strip():
        raise ValueError("schema name must be a non-empty string")

    normalized = name.strip()
    catalog = _catalog_schemas()

    candidates = catalog.get(normalized, [])
    if version:
        filtered = [item for item in candidates if item[0] == version]
        if not filtered:
            # Fallback to direct filesystem check in case the cache missed it
            for root in _iter_schema_roots():
                candidate_path = root / version / f"{normalized}{_SCHEMA_SUFFIX}"
                if candidate_path.exists():
                    schema_data = _load_schema(candidate_path)
                    return _build_response(
                        name=normalized,
                        version=version,
                        source=candidate_path,
                        schema=schema_data,
                    )
            return _build_response(
                name=normalized,
                version=version,
                source=Path(version),
                ok=False,
                reason=f"schema_not_found:{normalized}:{version}",
            )
        candidates = filtered

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

    return _build_response(
        name=normalized,
        version=selected_version,
        source=selected_path,
        schema=schema_payload,
    )


__all__ = ["get_schema", "list_schemas"]
