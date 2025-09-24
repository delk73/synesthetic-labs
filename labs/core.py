"""Core utilities for environment and path handling."""

from __future__ import annotations

from pathlib import Path


class PathTraversalError(ValueError):
    """Raised when a path attempts to traverse outside the allowed scope."""


def normalize_resource_path(value: str) -> str:
    """Normalize *value* to an absolute path and reject traversal components."""

    if not value:
        raise ValueError("path must be a non-empty string")

    candidate = Path(value).expanduser()
    if any(part == ".." for part in candidate.parts):
        raise PathTraversalError("path may not contain '..' segments")

    if candidate.is_absolute():
        normalized = candidate
    else:
        normalized = (Path.cwd() / candidate)

    return str(normalized.resolve(strict=False))


__all__ = ["PathTraversalError", "normalize_resource_path"]
