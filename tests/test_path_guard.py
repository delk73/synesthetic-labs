"""Tests for the core path normalization helpers."""

from __future__ import annotations

import os

import pytest

from labs.core import PathTraversalError, normalize_resource_path


def test_normalize_resource_path_relative(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    path = normalize_resource_path("schemas")
    assert path.startswith(os.fspath(tmp_path))
    assert path.endswith("schemas")


def test_normalize_resource_path_absolute(tmp_path) -> None:
    absolute = normalize_resource_path(str(tmp_path / "schemas"))
    assert absolute.endswith("schemas")


def test_normalize_resource_path_rejects_traversal() -> None:
    with pytest.raises(PathTraversalError):
        normalize_resource_path("../secrets")
