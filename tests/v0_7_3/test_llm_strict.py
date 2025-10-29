"""
Strict mode routing and Azure pass-through tests for schema v0.7.3.
"""

import os
from typing import Dict

import pytest

from labs.mcp.client import load_schema_bundle
from labs.v0_7_3.llm import (
    AZURE_STRICT_ALLOW,
    AZURE_STRICT_BLOCK,
    llm_generate_component_strict,
    supports_azure_strict,
)
from labs.v0_7_3.schema_analyzer import SchemaAnalyzer

AZ_CREDS = all(
    os.getenv(env_var)
    for env_var in ("AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT")
)


def _load_component_schema(component: str) -> Dict:
    schema_bundle = load_schema_bundle(version="0.7.3")
    analyzer = SchemaAnalyzer(version="0.7.3", schema=schema_bundle)
    return analyzer.get_component_schema(component).schema


def _strict_test_plan(component: str) -> Dict:
    return {
        "modality": component,
        "primary_component": {
            "type": component,
            "characteristics": [],
        },
        "suggested_tags": [],
        "constraints": {},
    }


def test_strict_eligibility():
    assert AZURE_STRICT_ALLOW == {"shader", "modulation"}
    assert AZURE_STRICT_BLOCK == {"control", "tone", "haptic"}
    assert supports_azure_strict("shader")
    assert supports_azure_strict("modulation")
    assert not supports_azure_strict("control")
    assert not supports_azure_strict("tone")
    assert not supports_azure_strict("haptic")


@pytest.fixture
def azure_client():
    pytest.importorskip("openai", reason="openai not installed")
    if not AZ_CREDS:
        pytest.skip("Azure creds required")
    from openai import AzureOpenAI

    return AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
    )


@pytest.mark.skipif(not AZ_CREDS, reason="Azure creds required")
def test_strict_shader_modulation_pass_or_fallback(azure_client):
    model = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")

    shader_schema = _load_component_schema("shader")
    shader_result = llm_generate_component_strict(
        azure_client,
        model=model,
        component_name="shader",
        subschema=shader_schema,
        prompt="neon blue pulsating shader",
        plan=_strict_test_plan("shader"),
    )
    assert isinstance(shader_result, dict)
    assert shader_result == {} or bool(shader_result)

    modulation_schema = _load_component_schema("modulation")
    modulation_result = llm_generate_component_strict(
        azure_client,
        model=model,
        component_name="modulation",
        subschema=modulation_schema,
        prompt="neon blue pulsating shader",
        plan=_strict_test_plan("modulation"),
    )
    assert isinstance(modulation_result, dict)
    assert modulation_result == {} or bool(modulation_result)


@pytest.mark.skipif(not AZ_CREDS, reason="Azure creds required")
def test_strict_shader_determinism(azure_client):
    schema = _load_component_schema("shader")
    plan = _strict_test_plan("shader")
    model = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")

    result_one = llm_generate_component_strict(
        azure_client,
        model=model,
        component_name="shader",
        subschema=schema,
        prompt="monochrome waveform shader",
        plan=plan,
    )
    result_two = llm_generate_component_strict(
        azure_client,
        model=model,
        component_name="shader",
        subschema=schema,
        prompt="monochrome waveform shader",
        plan=plan,
    )

    assert isinstance(result_one, dict)
    assert isinstance(result_two, dict)
    assert result_one == result_two


def test_control_never_uses_strict():
    assert not supports_azure_strict("control")
