---
version: v0.7.3-phase-7
status: next-phase-spec
parent: docs/labs_spec.md#phase-3-generator-implementation
---

# Phase 7: Component Generation (v0.7.3)

## Current State

✅ **Infrastructure Complete** (Phases 1-6):
- MCP client working (TCP, inline resolution)
- Test framework (23 tests, 22 passing)
- Minimal generator (returns valid but empty assets)
- Telemetry layer (separation validated)
- CI/CD (GitHub Actions ready)
- Documentation (README, CLI)

⚠️ **Current Limitation**:
```python
# What we generate now:
{
  "$schema": "...",
  "name": "red_pulsing_shader",
  "meta_info": {}
}
# Valid, but no actual shader/tone/haptic content!
```

## Goal: Schema-Driven Component Builders

Build **component generators** that populate shader, tone, haptic, control, modulation fields based on:
1. Schema structure (derive from MCP bundle)
2. User prompt (semantic extraction)
3. LLM guidance (Azure OpenAI structured output)

---

## 7.1 · Schema Analysis

### Current 0.7.3 Schema Structure

```python
# From MCP schema bundle
{
  "required": ["name"],
  "properties": {
    "name": {"type": "string"},
    "shader": { 
      # Complex nested structure with type, content, tags
      # Need to understand schema to generate valid content
    },
    "tone": { ... },
    "haptic": { ... },
    "control": { ... },
    "modulations": [ ... ],
    "rule_bundle": { ... }
  }
}
```

**Action**: Create `labs/v0_7_3/schema_analyzer.py` that:
- Parses schema bundle
- Extracts component subschemas
- Identifies required/optional fields per component
- Maps field constraints (enums, patterns, ranges)

---

## 7.2 · Component Builders

### Architecture

```
labs/v0_7_3/
├── generator.py           # Existing (orchestrator)
├── schema_analyzer.py     # New - schema introspection
└── components/            # New - component builders
    ├── __init__.py
    ├── shader.py          # build_shader(prompt, subschema)
    ├── tone.py            # build_tone(prompt, subschema)
    ├── haptic.py          # build_haptic(prompt, subschema)
    ├── control.py         # build_control(prompt, subschema)
    ├── modulation.py      # build_modulation(prompt, subschema)
    └── rule_bundle.py     # build_rule_bundle(prompt, subschema)
```

### Pattern: Schema-Driven Builders

```python
# labs/v0_7_3/components/shader.py

def build_shader(prompt: str, subschema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate shader component from prompt and schema.
    
    NO HARDCODED TEMPLATES - structure derived from subschema.
    """
    # 1. Analyze subschema
    required = subschema.get("required", [])
    properties = subschema.get("properties", {})
    
    # 2. Extract prompt semantics
    shader_type = infer_shader_type(prompt)  # "glsl", "hlsl", etc.
    tags = extract_tags(prompt)  # ["color", "animation", "pulse"]
    
    # 3. Build component matching schema
    shader = {}
    for field in required:
        if field == "type":
            shader["type"] = shader_type
        elif field == "content":
            shader["content"] = generate_shader_code(prompt, shader_type)
        elif field == "tags":
            shader["tags"] = tags
        # ... handle other required fields
    
    return shader
```

---

## 7.3 · LLM Integration (Azure Structured Output)

### Current Issue

Azure OpenAI structured output works at the **asset level**, but we need **component-level** guidance:

```python
# Current (works but gives minimal content):
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "red pulsing shader"}],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "SynestheticAsset_0_7_3",
            "schema": full_asset_schema  # TOO BROAD
        }
    }
)
```

### Proposed: Two-Stage Generation

**Stage 1: Semantic Decomposition**
```python
# Ask LLM to analyze prompt and plan components
decomposition = llm_decompose_prompt(
    "red pulsing shader with heartbeat rhythm"
)
# Returns:
{
  "modality": "shader",
  "primary_component": {
    "type": "shader",
    "characteristics": ["color:red", "animation:pulse", "rhythm:heartbeat"]
  },
  "suggested_tags": ["color", "animation", "rhythmic"],
  "constraints": {
    "shader_type": "glsl",
    "animation_frequency": "60-80 bpm"
  }
}
```

**Stage 2: Component-Specific Generation**
```python
# Generate each component with its subschema
shader_content = llm_generate_component(
    component_type="shader",
    subschema=asset_schema["properties"]["shader"],
    decomposition=decomposition,
    constraints={"type": "glsl"}
)
```

---

## 7.4 · Prompt Semantic Extraction

### Pattern Recognition

```python
# labs/v0_7_3/prompt_parser.py

def parse_prompt(prompt: str) -> Dict[str, Any]:
    """
    Extract semantic structure from user prompt.
    
    Examples:
      "red pulsing shader" → {modality: "shader", color: "red", animation: "pulse"}
      "ambient tone at 440Hz" → {modality: "tone", frequency: 440, style: "ambient"}
      "haptic vibration pattern" → {modality: "haptic", pattern: "vibration"}
    """
    semantics = {
        "modality": detect_modality(prompt),  # shader|tone|haptic|control
        "attributes": extract_attributes(prompt),
        "constraints": extract_constraints(prompt)
    }
    return semantics
```

**Modality Detection**:
- Keywords: "shader", "tone", "sound", "haptic", "vibration", "control"
- Context clues: "GLSL", "Hz", "frequency", "tactile"
- Fallback: If ambiguous, generate minimal asset (current behavior)

---

## 7.5 · Test-Driven Implementation

### TDD Flow

```python
# tests/v0_7_3/components/test_shader_builder.py

def test_shader_builder_generates_glsl():
    """Shader builder produces valid GLSL code."""
    from labs.v0_7_3.components.shader import build_shader
    from labs.mcp.client import load_schema_bundle
    
    bundle = load_schema_bundle(version="0.7.3")
    shader_subschema = bundle["properties"]["shader"]
    
    # Generate shader component
    shader = build_shader("red pulsing effect", shader_subschema)
    
    # Verify structure
    assert shader["type"] == "glsl"
    assert "content" in shader
    assert len(shader["content"]) > 0  # Has actual code
    assert "red" in shader["content"].lower()  # Prompt reflected
    
    # Validate against subschema
    # (use jsonschema library to validate component)
    validate(shader, shader_subschema)

def test_shader_integrated_in_asset():
    """Generated shader integrates into full asset."""
    asset = generate_asset("red shader", use_llm=False)
    
    # Asset should have populated shader
    assert "shader" in asset
    assert asset["shader"]["type"] == "glsl"
    assert "content" in asset["shader"]
    
    # Validate full asset via MCP
    client = MCPClient(schema_version="0.7.3")
    result = client.confirm(asset, strict=True)
    assert result["ok"] is True
```

---

## 7.6 · Implementation Checklist

### Immediate (Phase 7a - Foundation)
- [ ] Create `labs/v0_7_3/schema_analyzer.py`
- [ ] Extract subschemas for each component type
- [ ] Create `labs/v0_7_3/components/` namespace
- [ ] Implement `shader.py` builder (minimal GLSL template)
- [ ] Write tests for shader builder
- [ ] Integrate shader builder into `generator.py`

### Short-Term (Phase 7b - LLM Enhancement)
- [ ] Implement prompt decomposition (semantic extraction)
- [ ] Add two-stage LLM generation
- [ ] Implement component-specific Azure calls
- [ ] Add `tone.py`, `haptic.py` builders
- [ ] Write integration tests

### Medium-Term (Phase 7c - Full Coverage)
- [ ] Implement all component builders (control, modulation, rule_bundle)
- [ ] Add prompt parser with modality detection
- [ ] Add constraints and validation per component
- [ ] Add fixtures with example prompts
- [ ] Document component generation patterns

---

## 7.7 · Example Target Output

### Input
```bash
make generate P='red pulsing shader with 60 BPM heartbeat rhythm'
```

### Current Output (Phase 6)
```json
{
  "$schema": "...",
  "name": "red_pulsing_shader_with_60_bpm_heartbeat_rhythm",
  "meta_info": {}
}
```

### Target Output (Phase 7 Complete)
```json
{
  "$schema": "...",
  "name": "red_pulsing_shader_with_60_bpm_heartbeat_rhythm",
  "shader": {
    "type": "glsl",
    "content": "uniform float time;\nvoid main() {\n  float pulse = sin(time * 3.14 * 2.0);\n  gl_FragColor = vec4(1.0, 0.0, 0.0, pulse);\n}",
    "tags": ["color", "animation", "rhythmic"]
  },
  "modulations": [
    {
      "type": "temporal",
      "target": "shader.time",
      "frequency": 60,
      "unit": "bpm"
    }
  ],
  "meta_info": {
    "description": "Red pulsing shader with 60 BPM heartbeat rhythm"
  }
}
```

---

## 7.8 · Success Criteria

**Phase 7 Complete When**:
1. ✅ Shader builder produces valid GLSL code
2. ✅ Generated assets have populated components (not just empty objects)
3. ✅ Prompt semantics reflected in output (e.g., "red" → red color in shader)
4. ✅ LLM-generated components pass MCP validation
5. ✅ At least 3 component types working (shader, tone, haptic)
6. ✅ Integration tests validate full asset generation
7. ✅ CLI produces usable assets for downstream consumers

---

## 7.9 · Non-Goals (Deferred)

- ❌ Real-time shader compilation/preview
- ❌ Audio synthesis for tone generation
- ❌ Haptic device integration
- ❌ Advanced DSP for modulation
- ❌ Multi-modal asset blending
- ❌ Asset versioning/evolution

**Focus**: Generate valid, schema-compliant assets with realistic content.  
**Not**: Run/render/play those assets (downstream responsibility).

---

## 7.10 · Next Action

**Start with shader builder (most common use case)**:

```bash
# 1. Create component namespace
mkdir -p labs/v0_7_3/components
touch labs/v0_7_3/components/__init__.py

# 2. Write failing test
# tests/v0_7_3/components/test_shader.py

# 3. Implement shader builder
# labs/v0_7_3/components/shader.py

# 4. Integrate into generator.py
# Update generate_asset() to call shader builder

# 5. Verify
make generate P='red shader'  # Should have shader content now
```

Ready to proceed with Phase 7a?
