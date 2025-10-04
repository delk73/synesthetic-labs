"""Pytest configuration for Synesthetic Labs."""

from __future__ import annotations

import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


import pytest


@pytest.fixture(autouse=True)
def _default_schema_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LABS_SCHEMA_VERSION", "0.7.4")
