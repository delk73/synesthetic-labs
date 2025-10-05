"""Unit tests for the AssetAssembler."""

from __future__ import annotations

from typing import Dict, Set

from labs.generator import AssetAssembler


def _parameter_names(asset: Dict[str, object]) -> Set[str]:
    names: Set[str] = set()
    for section_key in ("shader", "tone", "haptic"):
        section = asset[section_key]
        for entry in section.get("input_parameters", []):  # type: ignore[assignment]
            parameter = entry.get("parameter")  # type: ignore[assignment]
            if parameter:
                names.add(parameter)
    return names
def test_asset_assembler_legacy_normalisation() -> None:
    assembler = AssetAssembler(schema_version="0.7.3")
    asset = assembler.generate("legacy schema", schema_version="0.7.3")

    assert asset["$schema"] == AssetAssembler.schema_url("0.7.3")
    assert isinstance(asset["name"], str)
    assert "asset_id" not in asset
    assert "parameter_index" not in asset
    assert "seed" not in asset
    assert asset["modulations"] == []
    assert asset["rule_bundle"]["rules"] == []
    assert set(asset.keys()) == {
        "$schema",
        "name",
        "shader",
        "tone",
        "haptic",
        "control",
        "modulations",
        "rule_bundle",
        "meta_info",
    }
    assert "input_parameters" not in asset["shader"]
    assert "effects" not in asset["tone"]
    assert "profile" not in asset["haptic"]
    assert asset["meta_info"].keys() == {"provenance"}
    assert isinstance(asset["meta_info"]["provenance"], dict)
    assert asset["control"]["control_parameters"]


def test_asset_assembler_enriched_normalisation() -> None:
    assembler = AssetAssembler(schema_version="0.7.4")
    asset = assembler.generate("enriched schema", schema_version="0.7.4")

    assert asset["$schema"] == AssetAssembler.schema_url("0.7.4")
    assert asset["prompt"] == "enriched schema"
    assert isinstance(asset["asset_id"], str)
    assert asset["parameter_index"]
    assert asset["provenance"]["agent"] == "AssetAssembler"

    parameters = _parameter_names(asset)
    assert parameters  # surfaces should not be empty

    for control_parameter in asset["control"]["control_parameters"]:
        assert control_parameter["parameter"] in parameters

    assert isinstance(asset["modulations"], list)
    assert asset["modulations"]
    assert asset["rule_bundle"]["rules"]
