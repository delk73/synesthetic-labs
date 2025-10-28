---
version: v0.7.3-phase-8
status: next-phase-spec
parent: docs/labs_spec.md#phase-7-component-generation
---

# Phase 8: Strict Mode LLM Generation (v0.7.3)

## Overview

**Goal**: Implement Azure structured output generation for components with closed schemas (control, modulation, shader).

**Scope**: Single generation mode using `json_schema` response format with strict validation.

**Out of Scope**: Flexible mode for tone/haptic (deferred to Phase 9).

---

## Current State

✅ **Phase 7 Complete**:
- Component builders implemented (shader, tone, haptic, control, modulation, rule_bundle)
- Schema analyzer with cross-reference resolution
- Prompt parser with semantic extraction
- LLM integration (Azure OpenAI) - two-stage decompose + generate
- 29 tests passing (v0.7.3)
- Assets generate with populated components

⚠️ **Blocking Issue**:
```
Azure structured output error:
"'additionalProperties' is required to be supplied and to be false"

Cause: 67 object schemas in 0.7.3 need additionalProperties:false recursively
```

---

## Problem Analysis

### Component Classification by Schema

```python
# From MCP schema analysis (0.7.3):
{
  "control":    {"additionalProperties": false},   # ✅ Phase 8 - strict mode
  "modulation": {"additionalProperties": false},   # ✅ Phase 8 - strict mode
  "shader":     {"additionalProperties": false},   # ✅ Phase 8 - strict mode
  "tone":       {"additionalProperties": true},    # ⏳ Phase 9 (flexible mode)
  "haptic":     {"additionalProperties": NOT SET}, # ⏳ Phase 9 (flexible mode)
}
```

### Why Strict Mode for These Three

1. **Control**: Simple parameter mappings, closed schema
2. **Modulation**: Envelope/oscillator configs, closed schema
3. **Shader**: GLSL code strings, closed schema structure

All three have `additionalProperties: false` already set → perfect candidates for Azure structured output.

### Azure Structured Output Requirements

- **ALL** object schemas must have `additionalProperties: false`
- Recursive application needed (nested objects, anyOf, items)
- Guarantees no hallucinated fields
- Maximum safety, zero schema drift

---

## Architecture Design

### Phase 8 Components

```python
# labs/v0_7_3/llm.py

# Phase 8: Strict mode only
STRICT_COMPONENTS = {
    'control',     # Parameter mappings
    'modulation',  # Envelopes/LFOs
    'shader',      # GLSL code
}

# Phase 9: Deferred
FLEXIBLE_COMPONENTS = {
    'tone',    # Tone.js extensibility
    'haptic',  # Device-specific
}
```

### Strict Mode Generation

```python
def llm_generate_component_strict(
    client: Any,
    *,
    model: str,
    component_name: str,
    subschema: Mapping[str, Any],
    prompt: str,
    plan: Dict[str, Any],
    fallback_semantics: Optional[PromptSemantics] = None,
) -> Dict[str, Any]:
    """
    Generate component using Azure structured output (strict validation).
    
    Phase 8: control, modulation, shader
    Azure validates schema compliance during generation.
    """
    from labs.v0_7_3.prompt_parser import parse_prompt
    import json
    
    schema_name = f"Synesthetic_{component_name.title().replace('_', '')}"
    semantics = fallback_semantics or parse_prompt(prompt)
    
    # Ensure subschema has additionalProperties:false everywhere
    strict_subschema = _ensure_strict_schema(subschema)
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    f"You generate {component_name} component JSON for synesthetic assets. "
                    "Strictly follow the provided JSON schema."
                ),
            },
            {
                "role": "user",
                "content": json.dumps({
                    "prompt": prompt,
                    "component": component_name,
                    "plan": plan,
                    "semantics": semantics.to_dict(),
                }, indent=2),
            },
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": schema_name,
                "schema": strict_subschema,
                "strict": True,
            },
        },
        temperature=0.0,  # Deterministic
    )
    
    payload = response.choices[0].message.content or "{}"
    try:
        data = json.loads(payload)
        if not isinstance(data, dict):
            raise ValueError("LLM response must be a JSON object")
        return data
    except json.JSONDecodeError as exc:
        print(f"Failed to parse LLM response for {component_name}: {exc}")
        return {}


def _ensure_strict_schema(subschema: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Recursively add additionalProperties:false to all object schemas.
    Handles anyOf/oneOf/allOf combinators and array items.
    """
    import copy
    
    schema = copy.deepcopy(subschema)
    
    def make_strict(obj):
        if isinstance(obj, dict):
            # Add additionalProperties:false to any object with properties
            if 'properties' in obj and 'additionalProperties' not in obj:
                obj['additionalProperties'] = False
            
            # Handle combinators
            for combinator in ['anyOf', 'oneOf', 'allOf']:
                if combinator in obj and isinstance(obj[combinator], list):
                    for item in obj[combinator]:
                        make_strict(item)
            
            # Handle array items
            if 'items' in obj:
                make_strict(obj['items'])
            
            # Recurse into nested values
            for key, value in obj.items():
                if key not in ['$ref', '$schema']:
                    make_strict(value)
        
        elif isinstance(obj, list):
            for item in obj:
                make_strict(item)
    
    make_strict(schema)
    return schema
```

---

## Generator Integration

```python
# labs/v0_7_3/generator.py

def _generate_with_azure(prompt: str, version: str = "0.7.3") -> Dict[str, Any]:
    """Generate asset using strict mode Azure LLM for control, modulation, shader."""
    import os
    from openai import AzureOpenAI
    from labs.mcp.validate import validate_asset
    from labs.mcp.client import load_schema_bundle
    from labs.v0_7_3.llm import llm_generate_component_strict, llm_decompose_prompt
    from labs.v0_7_3.schema_analyzer import SchemaAnalyzer
    from labs.v0_7_3.components import (
        build_shader, build_tone, build_haptic,
        build_control, build_modulation, build_rule_bundle
    )
    
    # Initialize Azure client
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
    )
    model_name = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
    
    # Initialize builders (fallback if LLM fails)
    builders = {
        'shader': build_shader,
        'tone': build_tone,
        'haptic': build_haptic,
        'control': build_control,
        'modulation': build_modulation,
        'rule_bundle': build_rule_bundle,
    }
    
    # Load schema
    schema_bundle = load_schema_bundle(version=version)
    analyzer = SchemaAnalyzer(version=version, schema=schema_bundle)
    
    # Initialize asset
    asset: Dict[str, Any] = {
        "$schema": f"https://delk73.github.io/synesthetic-schemas/schema/{version}/synesthetic-asset.schema.json",
        "name": _sanitize_name(prompt),
    }
    
    # Stage 1: Decompose prompt
    plan = llm_decompose_prompt(client, model=model_name, prompt=prompt)
    
    # Stage 2: Detect which components to generate
    components_to_generate = _detect_components(prompt, plan)
    
    # Stage 3: Generate components
    for component_name in components_to_generate:
        subschema = analyzer.get_component_schema(component_name)
        
        # Phase 8: Only strict mode for control, modulation, shader
        if component_name in {'control', 'modulation', 'shader'}:
            try:
                component_data = llm_generate_component_strict(
                    client,
                    model=model_name,
                    component_name=component_name,
                    subschema=subschema,
                    prompt=prompt,
                    plan=plan,
                )
            except Exception as e:
                print(f"LLM generation failed for {component_name}: {e}")
                component_data = builders[component_name](prompt, subschema)
        else:
            # Fallback to builders for tone/haptic (Phase 9 will add flexible mode)
            component_data = builders[component_name](prompt, subschema)
        
        asset[component_name] = component_data
    
    # Final validation
    validation = validate_asset(asset)
    if not validation["ok"]:
        raise ValueError(f"Generated asset failed validation: {validation}")
    
    return asset


def _detect_components(prompt: str, plan: Dict[str, Any]) -> List[str]:
    """Determine which components to generate from prompt and plan."""
    components = []
    
    modality = plan.get('modality', 'mixed')
    prompt_lower = prompt.lower()
    
    # Shader keywords
    if modality == 'shader' or any(kw in prompt_lower for kw in ['shader', 'glsl', 'color', 'visual', 'red', 'blue', 'green']):
        components.append('shader')
    
    # Tone keywords (Phase 9)
    if modality == 'tone' or any(kw in prompt_lower for kw in ['tone', 'sound', 'audio', 'hz', 'frequency']):
        components.append('tone')
    
    # Haptic keywords (Phase 9)
    if modality == 'haptic' or any(kw in prompt_lower for kw in ['haptic', 'vibration', 'tactile', 'rumble']):
        components.append('haptic')
    
    # Control keywords
    if any(kw in prompt_lower for kw in ['control', 'parameter', 'mapping', 'input']):
        components.append('control')
    
    # Modulation keywords
    if any(kw in prompt_lower for kw in ['modulation', 'envelope', 'lfo', 'oscillate', 'pulse']):
        components.append('modulation')
    
    # Fallback: at least shader
    if not components:
        components.append('shader')
    
    return components


def _sanitize_name(prompt: str) -> str:
    """Generate a valid asset name from prompt."""
    import re
    # Take first 50 chars, replace non-alphanumeric with underscores
    name = re.sub(r'[^a-zA-Z0-9_]', '_', prompt[:50])
    return name.strip('_').lower() or 'untitled_asset'
```

---

## Test Strategy

```python
# tests/v0_7_3/test_strict_mode_llm.py

import os
import pytest


def test_strict_mode_control():
    """Control generation uses Azure strict structured output."""
    if not os.getenv("AZURE_OPENAI_API_KEY"):
        pytest.skip("Azure credentials not available")
    
    from labs.v0_7_3.llm import llm_generate_component_strict
    from labs.mcp.client import load_schema_bundle
    from labs.v0_7_3.schema_analyzer import SchemaAnalyzer
    from openai import AzureOpenAI
    
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
    )
    
    schema = load_schema_bundle(version="0.7.3")
    analyzer = SchemaAnalyzer(version="0.7.3", schema=schema)
    subschema = analyzer.get_component_schema('control')
    
    plan = {"modality": "mixed", "intent": "control parameters"}
    control = llm_generate_component_strict(
        client,
        model="gpt-4o-mini",
        component_name="control",
        subschema=subschema,
        prompt="map mouse position to color intensity",
        plan=plan
    )
    
    assert isinstance(control, dict)
    assert 'control_parameters' in control


def test_strict_mode_modulation():
    """Modulation generation uses Azure strict structured output."""
    if not os.getenv("AZURE_OPENAI_API_KEY"):
        pytest.skip("Azure credentials not available")
    
    from labs.v0_7_3.llm import llm_generate_component_strict
    from labs.mcp.client import load_schema_bundle
    from labs.v0_7_3.schema_analyzer import SchemaAnalyzer
    from openai import AzureOpenAI
    
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
    )
    
    schema = load_schema_bundle(version="0.7.3")
    analyzer = SchemaAnalyzer(version="0.7.3", schema=schema)
    subschema = analyzer.get_component_schema('modulation')
    
    plan = {"modality": "mixed", "intent": "modulation envelope"}
    modulation = llm_generate_component_strict(
        client,
        model="gpt-4o-mini",
        component_name="modulation",
        subschema=subschema,
        prompt="pulsing envelope with 1 second attack",
        plan=plan
    )
    
    assert isinstance(modulation, dict)


def test_strict_mode_shader():
    """Shader generation uses Azure strict structured output."""
    if not os.getenv("AZURE_OPENAI_API_KEY"):
        pytest.skip("Azure credentials not available")
    
    from labs.v0_7_3.llm import llm_generate_component_strict
    from labs.mcp.client import load_schema_bundle
    from labs.v0_7_3.schema_analyzer import SchemaAnalyzer
    from openai import AzureOpenAI
    
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
    )
    
    schema = load_schema_bundle(version="0.7.3")
    analyzer = SchemaAnalyzer(version="0.7.3", schema=schema)
    subschema = analyzer.get_component_schema('shader')
    
    plan = {"modality": "shader", "intent": "red color"}
    shader = llm_generate_component_strict(
        client,
        model="gpt-4o-mini",
        component_name="shader",
        subschema=subschema,
        prompt="red pulsing shader",
        plan=plan
    )
    
    assert isinstance(shader, dict)
    assert 'fragment_shader' in shader


def test_ensure_strict_schema_adds_additional_properties():
    """_ensure_strict_schema adds additionalProperties:false recursively."""
    from labs.v0_7_3.llm import _ensure_strict_schema
    
    schema = {
        'type': 'object',
        'properties': {
            'nested': {
                'type': 'object',
                'properties': {
                    'value': {'type': 'string'}
                }
            }
        }
    }
    
    strict = _ensure_strict_schema(schema)
    
    assert strict['additionalProperties'] is False
    assert strict['properties']['nested']['additionalProperties'] is False


def test_ensure_strict_schema_handles_any_of():
    """_ensure_strict_schema traverses anyOf combinators."""
    from labs.v0_7_3.llm import _ensure_strict_schema
    
    schema = {
        'anyOf': [
            {
                'type': 'object',
                'properties': {'a': {'type': 'string'}}
            },
            {
                'type': 'object',
                'properties': {'b': {'type': 'number'}}
            }
        ]
    }
    
    strict = _ensure_strict_schema(schema)
    
    assert strict['anyOf'][0]['additionalProperties'] is False
    assert strict['anyOf'][1]['additionalProperties'] is False


def test_ensure_strict_schema_handles_array_items():
    """_ensure_strict_schema traverses array items."""
    from labs.v0_7_3.llm import _ensure_strict_schema
    
    schema = {
        'type': 'array',
        'items': {
            'type': 'object',
            'properties': {'id': {'type': 'string'}}
        }
    }
    
    strict = _ensure_strict_schema(schema)
    
    assert strict['items']['additionalProperties'] is False


def test_detect_components_from_prompt():
    """_detect_components extracts components from prompt keywords."""
    from labs.v0_7_3.generator import _detect_components
    
    plan = {"modality": "mixed"}
    
    # Shader keywords
    components = _detect_components("red pulsing visual", plan)
    assert 'shader' in components
    
    # Multiple components
    components = _detect_components("blue tone with haptic feedback and control", plan)
    assert 'shader' in components
    assert 'tone' in components
    assert 'haptic' in components
    assert 'control' in components


def test_azure_generator_validates():
    """Integration test: Full asset generation with Azure strict mode."""
    if not os.getenv("AZURE_OPENAI_API_KEY"):
        pytest.skip("Azure credentials not available")
    
    from labs.v0_7_3.generator import generate_asset
    
    prompt = "red pulsing shader with control parameters"
    asset = generate_asset(prompt, use_llm=True, engine="azure")
    
    # Verify shader component
    assert "shader" in asset
    assert "fragment_shader" in asset["shader"]
    
    # Verify control component (if detected)
    if "control" in asset:
        assert "control_parameters" in asset["control"]
    
    # Validate via MCP
    from labs.mcp.validate import validate_asset
    result = validate_asset(asset)
    assert result["ok"] is True
```

---

## Implementation Checklist

### Phase 8 - Strict Mode Only

- [ ] Implement `llm_generate_component_strict()` in `labs/v0_7_3/llm.py`
- [ ] Implement `_ensure_strict_schema()` helper (deep traversal)
- [ ] Update `_generate_with_azure()` in `labs/v0_7_3/generator.py`
- [ ] Implement `_detect_components()` helper
- [ ] Implement `_sanitize_name()` helper
- [ ] Write test for control component generation
- [ ] Write test for modulation component generation
- [ ] Write test for shader component generation
- [ ] Write tests for `_ensure_strict_schema()` (nested, anyOf, items)
- [ ] Write test for `_detect_components()`
- [ ] Update `test_azure_generator_validates` to run (no longer skipped)
- [ ] Document strict mode in README

---

## Success Criteria

**Phase 8 Complete When**:

1. ✅ `llm_generate_component_strict()` implemented with temperature=0.0
2. ✅ `_ensure_strict_schema()` handles deep traversal (anyOf, items)
3. ✅ Control components generated via Azure structured output
4. ✅ Modulation components generated via Azure structured output
5. ✅ Shader components generated via Azure structured output
6. ✅ Fallback to builders works on LLM exceptions
7. ✅ All strict mode tests pass
8. ✅ `test_azure_generator_validates` runs and passes (not skipped)
9. ✅ MCP validation passes for all generated assets

---

## Benefits

**Architectural Advantages**:
- ✅ **Focused scope**: Single mode, clear implementation
- ✅ **Schema-driven**: Uses actual schema constraints
- ✅ **Resilient**: Fallback to builders on failure
- ✅ **Simple**: No routing complexity
- ✅ **MCP authority**: All validation through MCP

**Practical Outcomes**:
- No MCP schema modifications needed
- Azure guarantees schema compliance
- Clear foundation for Phase 9 (flexible mode)
- Deterministic generation (temperature=0.0)

---

## Phase 9 Preview - Deferred Features

**Flexible Mode (Tone & Haptic)**:
- Use Azure `json_object` response format
- Post-generation validation via MCP
- Handle Tone.js extensibility
- Device-specific haptic parameters

**Advanced Shader Validation**:
- GLSL code linting (main(), gl_FragColor)
- Uniform consistency checking
- Syntax validation

**Telemetry & Metrics**:
- Generation timing
- LLM vs builder usage
- Failure mode analysis

---

## Next Steps

```bash
# 1. Implement llm_generate_component_strict()
# labs/v0_7_3/llm.py

# 2. Implement _ensure_strict_schema() helper
# labs/v0_7_3/llm.py

# 3. Update _generate_with_azure() integration
# labs/v0_7_3/generator.py

# 4. Implement helper functions
# - _detect_components()
# - _sanitize_name()

# 5. Write unit tests
# tests/v0_7_3/test_strict_mode_llm.py

# 6. Run integration test
pytest tests/v0_7_3/test_generator.py::test_azure_generator_validates -v
```
