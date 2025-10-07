from pathlib import Path

import pytest

from labs.mcp import validate


def _expected_schema_path(*parts: str) -> Path:
    return (validate._ROOT / Path("meta") / "schemas" / Path(*parts)).resolve()


def test_resolve_remote_schema_path_with_version_0_7_3():
    identifier = (
        "https://schemas.synesthetic-labs.ai/mcp/0.7.3/"
        "synesthetic-asset.schema.json"
    )

    resolved = validate._resolve_schema_path(identifier)

    assert resolved == _expected_schema_path("0.7.3", "synesthetic-asset.schema.json")


def test_resolve_remote_schema_path_with_version_0_7_4():
    identifier = (
        "https://schemas.synesthetic-labs.ai/mcp/0.7.4/"
        "synesthetic-asset.schema.json"
    )

    resolved = validate._resolve_schema_path(identifier)

    assert resolved == _expected_schema_path("0.7.4", "synesthetic-asset.schema.json")


def test_resolve_local_relative_schema_path():
    identifier = "meta/schemas/0.7.3/synesthetic-asset.schema.json"

    resolved = validate._resolve_schema_path(identifier)

    expected = _expected_schema_path("0.7.3", "synesthetic-asset.schema.json")
    assert resolved == expected
    assert resolved.is_absolute()


def test_resolve_schema_path_requires_filename():
    identifier = "https://schemas.synesthetic-labs.ai/mcp/0.7.3/"

    with pytest.raises(ValueError):
        validate._resolve_schema_path(identifier)


def test_load_validator_is_cached():
    identifier = "meta/schemas/0.7.3/synesthetic-asset.schema.json"

    validate._VALIDATOR_CACHE.clear()

    first = validate._load_validator(identifier)
    second = validate._load_validator(identifier)

    assert first is second
