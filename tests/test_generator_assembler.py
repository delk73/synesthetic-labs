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

    assert asset["$schema"] == AssetAssembler.schema_url_for_version("0.7.3")
    assert asset["name"]
    assert "asset_id" not in asset
    assert "prompt" not in asset
    assert "provenance" not in asset

    meta_info = asset["meta_info"]
    provenance = meta_info["provenance"]
    assert provenance["asset_id"]
    assert provenance.get("schema_version") == "0.7.3"
    assert AssetAssembler.resolve_asset_id(asset) == provenance["asset_id"]

    parameters = _parameter_names(asset)
    assert parameters

    for control_parameter in asset["control"]["control_parameters"]:
        assert control_parameter["parameter"] in parameters

    assert isinstance(asset["modulations"], list)
    assert asset["modulations"]
    assert asset["rule_bundle"]["rules"]


def test_asset_assembler_produces_enriched_payload() -> None:
    assembler = AssetAssembler()
    asset = assembler.generate("assembler enriched", schema_version="0.7.4")

    assert asset["$schema"] == AssetAssembler.schema_url_for_version("0.7.4")
    assert asset["asset_id"]
    assert asset["prompt"] == "assembler enriched"
    assert asset["provenance"]["schema_version"] == "0.7.4"
    assert "name" not in asset

    parameters = _parameter_names(asset)
    assert parameters
    assert sorted(parameters) == asset["parameter_index"]

    for control_parameter in asset["control"]["control_parameters"]:
        assert control_parameter["parameter"] in parameters

    assert isinstance(asset["modulations"], list)
    assert asset["modulations"]
    assert asset["rule_bundle"]["rules"]
