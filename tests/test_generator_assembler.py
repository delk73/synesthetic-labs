"""Unit tests for the AssetAssembler."""

from __future__ import annotations

import os
from typing import Dict, Set

import pytest

from labs.cli import SocketMCPValidator
from labs.generator import AssetAssembler
from labs.agents.critic import MCPUnavailableError


def _parameter_names(asset: Dict[str, object]) -> Set[str]:
    names: Set[str] = set()
    for section_key in ("shader", "tone", "haptic"):
        section = asset[section_key]
        for entry in section.get("input_parameters", []):  # type: ignore[assignment]
            parameter = entry.get("parameter")  # type: ignore[assignment]
            if parameter:
                names.add(parameter)
    return names


def _maybe_validate_with_mcp(asset: Dict[str, object]) -> Dict[str, object]:
    host = os.getenv("MCP_HOST")
    port_value = os.getenv("MCP_PORT")
    schemas_dir = os.getenv("SYN_SCHEMAS_DIR")

    if not host or not port_value or not schemas_dir:
        pytest.skip("MCP validation requires MCP_HOST, MCP_PORT, and SYN_SCHEMAS_DIR")

    try:
        port = int(port_value)
    except (TypeError, ValueError):
        pytest.skip("MCP_PORT is not a valid integer")

    validator = SocketMCPValidator(host, port)
    try:
        return validator.validate(asset)
    except (MCPUnavailableError, OSError) as exc:
        pytest.skip(f"MCP unavailable: {exc}")


def test_asset_assembler_produces_consistent_payload() -> None:
    assembler = AssetAssembler()
    asset = assembler.generate("assembler smoke test")

    assert asset["prompt"] == "assembler smoke test"
    assert isinstance(asset["id"], str)
    assert asset["provenance"]["agent"] == "AssetAssembler"

    parameters = _parameter_names(asset)
    assert parameters  # surfaces should not be empty

    for mapping in asset["control"]["mappings"]:
        assert mapping["parameter"] in parameters

    for modulator in asset["modulation"]["modulators"]:
        assert modulator["target"] in parameters

    for rule in asset["rule_bundle"]["rules"]:
        for effect in rule["effects"]:
            target = effect.get("target")
            if target is not None:
                assert target in parameters


def test_asset_assembler_output_validates_with_mcp() -> None:
    assembler = AssetAssembler()
    asset = assembler.generate("assembler validation test")

    response = _maybe_validate_with_mcp(asset)
    assert isinstance(response, dict)
