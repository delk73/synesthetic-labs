"""Schema validation tests for Synesthetic assets."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from labs.generator import AssetAssembler
from labs.generator.external import AzureOpenAIGenerator

SCHEMA_ROOT = Path("meta/schemas")


def _load_schema(version: str) -> dict:
    schema_path = SCHEMA_ROOT / version / "synesthetic-asset.schema.json"
    return json.loads(schema_path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("schema_version", ["0.7.3", "0.7.4"])
def test_internal_asset_matches_schema(schema_version: str) -> None:
    assembler = AssetAssembler(schema_version=schema_version)
    asset = assembler.generate(
        "schema validation internal",
        seed=99,
        schema_version=schema_version,
    )

    schema = _load_schema(schema_version)
    jsonschema.Draft202012Validator(schema).validate(asset)


@pytest.mark.parametrize("schema_version", ["0.7.3", "0.7.4"])
def test_external_asset_matches_schema(schema_version: str) -> None:
    generator = AzureOpenAIGenerator(mock_mode=True, sleeper=lambda _: None)
    asset, _context = generator.generate(
        "schema validation external",
        schema_version=schema_version,
    )

    schema = _load_schema(schema_version)
    jsonschema.Draft202012Validator(schema).validate(asset)

