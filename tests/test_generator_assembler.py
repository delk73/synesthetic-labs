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


def test_asset_assembler_produces_consistent_payload() -> None:
    assembler = AssetAssembler()
    asset = assembler.generate("assembler smoke test")

    assert asset["prompt"] == "assembler smoke test"
    assert isinstance(asset["asset_id"], str)
    assert asset["$schema"] == AssetAssembler.SCHEMA_URL
    assert asset["provenance"]["agent"] == "AssetAssembler"

    parameters = _parameter_names(asset)
    assert parameters  # surfaces should not be empty

    for control_parameter in asset["control"]["control_parameters"]:
        assert control_parameter["parameter"] in parameters

    assert isinstance(asset["modulations"], list)
    assert asset["modulations"]
    assert asset["rule_bundle"]["rules"]
