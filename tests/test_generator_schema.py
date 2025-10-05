"""Schema validation tests for Synesthetic assets."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from labs.generator import AssetAssembler
from labs.generator.external import GeminiGenerator

SCHEMA_PATH = Path("meta/schemas/synesthetic-asset.schema.json")


LEGACY_SCHEMA = {
    "type": "object",
    "required": [
        "$schema",
        "name",
        "shader",
        "tone",
        "haptic",
        "control",
        "modulations",
        "rule_bundle",
        "meta_info",
    ],
    "properties": {
        "$schema": {"type": "string"},
        "name": {"type": "string"},
        "shader": {"type": "object"},
        "tone": {"type": "object"},
        "haptic": {"type": "object"},
        "control": {"type": "object"},
        "modulations": {"type": "array"},
        "rule_bundle": {"type": "object"},
        "meta_info": {
            "type": "object",
            "required": ["provenance"],
            "properties": {
                "provenance": {
                    "type": "object",
                    "required": ["asset_id"],
                    "properties": {
                        "asset_id": {"type": "string"},
                        "schema_version": {"type": "string"},
                    },
                }
            },
        },
    },
    "additionalProperties": True,
}


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_internal_asset_matches_schema() -> None:
    assembler = AssetAssembler()
    asset = assembler.generate("schema validation internal", seed=99, schema_version="0.7.4")

    schema = _load_schema()
    jsonschema.Draft202012Validator(schema).validate(asset)


def test_internal_asset_legacy_matches_schema() -> None:
    assembler = AssetAssembler()
    asset = assembler.generate("schema validation internal legacy", seed=42, schema_version="0.7.3")

    jsonschema.Draft202012Validator(LEGACY_SCHEMA).validate(asset)


def test_external_asset_matches_schema() -> None:
    generator = GeminiGenerator(mock_mode=True, sleeper=lambda _: None)
    asset, _context = generator.generate("schema validation external", schema_version="0.7.4")

    schema = _load_schema()
    jsonschema.Draft202012Validator(schema).validate(asset)


def test_external_asset_legacy_matches_schema() -> None:
    generator = GeminiGenerator(mock_mode=True, sleeper=lambda _: None)
    asset, _context = generator.generate("schema validation external legacy", schema_version="0.7.3")

    jsonschema.Draft202012Validator(LEGACY_SCHEMA).validate(asset)

