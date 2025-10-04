"""Schema validation tests for Synesthetic assets."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from labs.generator import AssetAssembler
from labs.generator.external import GeminiGenerator

SCHEMA_PATH = Path("meta/schemas/synesthetic-asset.schema.json")


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_internal_asset_matches_schema() -> None:
    assembler = AssetAssembler()
    asset = assembler.generate("schema validation internal", seed=99)

    schema = _load_schema()
    jsonschema.Draft202012Validator(schema).validate(asset)


def test_external_asset_matches_schema() -> None:
    generator = GeminiGenerator(mock_mode=True, sleeper=lambda _: None)
    asset, _context = generator.generate("schema validation external")

    schema = _load_schema()
    jsonschema.Draft202012Validator(schema).validate(asset)

