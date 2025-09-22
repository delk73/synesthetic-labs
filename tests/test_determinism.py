"""Determinism checks for the asset assembler."""

from __future__ import annotations

import json

from labs.generator.assembler import AssetAssembler


def test_asset_is_deterministic_with_seed() -> None:
    assembler = AssetAssembler()
    prompt = "deterministic baseline"

    first = assembler.generate(prompt, seed=123)
    second = assembler.generate(prompt, seed=123)

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_asset_varies_without_seed() -> None:
    assembler = AssetAssembler()
    prompt = "deterministic baseline"

    first = assembler.generate(prompt)
    second = assembler.generate(prompt)

    assert json.dumps(first, sort_keys=True) != json.dumps(second, sort_keys=True)
