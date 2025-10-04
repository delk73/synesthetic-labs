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


def test_asset_assembler_produces_legacy_payload() -> None:
    assembler = AssetAssembler()
    asset = assembler.generate("assembler smoke test")

    assert asset["prompt"] == "assembler smoke test"
    assert isinstance(asset["asset_id"], str)
    assert asset["$schema"] == AssetAssembler.schema_url_for("0.7.3")
    assert "provenance" in asset

    parameters = _parameter_names(asset)
    assert parameters  # surfaces should not be empty

    for control_parameter in asset["control"]["control_parameters"]:
        assert control_parameter["parameter"] in parameters

    assert isinstance(asset["modulations"], list)
    assert asset["modulations"]
    assert asset["rule_bundle"]["rules"]

    meta_provenance = asset["meta_info"]["provenance"]
    asset_provenance = meta_provenance["asset"]
    assert asset_provenance["agent"] == "AssetAssembler"


def test_asset_assembler_produces_enriched_payload() -> None:
    assembler = AssetAssembler(schema_version="0.7.4")
    asset = assembler.generate("assembler enriched", schema_version="0.7.4")

    assert asset["prompt"] == "assembler enriched"
    assert asset["$schema"] == AssetAssembler.schema_url_for("0.7.4")
    assert asset["provenance"]["agent"] == "AssetAssembler"
    assert asset["meta_info"]["title"] == "assembler enriched"
    assert "parameter_index" in asset
