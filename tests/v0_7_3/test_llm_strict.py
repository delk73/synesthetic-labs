"""Strict mode tests for schema v0.7.3 (hard mode)."""

from __future__ import annotations

import json
import sys
import types
from typing import Any

import pytest

from labs.mcp.client import MCPClient
from labs.v0_7_3.generator import generate_asset
from labs.v0_7_3.llm import (
    STRICT_COMPONENTS,
    StrictGenerationError,
    generate_strict_component,
    llm_generate_component_strict,
)
from labs.v0_7_3.schema_analyzer import SchemaAnalyzer


class _FakeAzure:
    class _Response:
        def __init__(self, content: str) -> None:
            message = types.SimpleNamespace(content=content)
            self.choices = [types.SimpleNamespace(message=message)]

    class _Completions:
        def __init__(self, payload: str) -> None:
            self._payload = payload

        def create(self, **_: Any) -> "_FakeAzure._Response":
            return _FakeAzure._Response(self._payload)

    class _Chat:
        def __init__(self, payload: str) -> None:
            self.completions = _FakeAzure._Completions(payload)

    def __init__(self, payload: str) -> None:
        self.chat = _FakeAzure._Chat(payload)


def test_generate_strict_component_success() -> None:
    schema = SchemaAnalyzer(version="0.7.3").get_component_schema("shader").schema
    payload = json.dumps({"fragment_shader": "void main(){}"})
    azure = _FakeAzure(payload)

    result = generate_strict_component(
        azure,
        model="test-model",
        component_name="shader",
        subschema=schema,
        prompt="minimal shader",
    )

    assert result == {"fragment_shader": "void main(){}"}


def test_generate_strict_component_invalid_json() -> None:
    schema = SchemaAnalyzer(version="0.7.3").get_component_schema("shader").schema
    azure = _FakeAzure("not-json")

    with pytest.raises(StrictGenerationError):
        generate_strict_component(
            azure,
            model="test-model",
            component_name="shader",
            subschema=schema,
            prompt="minimal shader",
        )


def test_llm_generate_component_strict_scope_enforcement() -> None:
    schema = SchemaAnalyzer(version="0.7.3").get_component_schema("shader").schema
    azure = _FakeAzure(json.dumps({"fragment_shader": "void main(){}"}))

    payload = llm_generate_component_strict(
        azure,
        model="test-model",
        component_name="shader",
        subschema=schema,
        prompt="minimal shader",
    )
    assert payload["fragment_shader"].startswith("void")

    with pytest.raises(ValueError):
        llm_generate_component_strict(
            azure,
            model="test-model",
            component_name="tone",
            subschema=schema,
            prompt="minimal shader",
        )


def test_generate_asset_strict(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = json.dumps({
        "name": "strict_shader_stub",
        "fragment_shader": "void main(){}",
        "vertex_shader": "void main(){}",
        "meta_info": None,
        "uniforms": [],
        "input_parameters": [],
    })


    class _StubAzure(_FakeAzure):
        pass

    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "stub-key")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://stub.example.com")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "stub-model")

    stub_module = types.SimpleNamespace(AzureOpenAI=lambda **_: _StubAzure(payload))
    monkeypatch.setitem(sys.modules, "openai", stub_module)

    asset = generate_asset("strict shader", use_llm=True, engine="azure")

    assert asset["name"] == "strict_shader"
    assert "shader" in asset
    assert asset["shader"]["fragment_shader"].startswith("void")

    client = MCPClient(schema_version="0.7.3")
    result = client.confirm(asset, strict=True)
    assert result["ok"] is True
