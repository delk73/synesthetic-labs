---

version: v0.7.3-phase-8
status: next-phase-spec
parent: docs/labs_spec.md#phase-7-component-generation
------------------------------------------------------

# Phase 8: Strict Mode LLM Generation (v0.7.3)

## Objective

Route **only closed, Azure-compatible components** through Azure strict `json_schema` generation **without any schema mutation**. Everything else uses schema-driven builders. MCP remains the sole schema authority.

## Scope

* **In**: `shader`, `modulation` via Azure **strict** structured output (pass-through schemas).
* **Out**: `control`, `tone`, `haptic` for strict mode (builder fallback only). Flexible mode is Phase 9.

## Ground Rules

1. **No schema edits** in Labs. No `$ref` deref, no `additionalProperties`, no `required` surgery, no `$schema` injection.
2. **Inline bundle from MCP only** (authority). Pass to Azure unchanged.
3. **Deterministic generation**: `temperature=0`, `max_tokens=2048`, fixed `seed` if supported.
4. **Hard allow/block lists** for strict eligibility.
5. **Fail-safe**: any strict path failure → builder fallback, then MCP validation.
6. **Telemetry separation**: never mix telemetry into assets sent to MCP or Azure.

## Decision Matrix (v0.7.3)

| Component    | Azure strict | Reason                                                          |
| ------------ | ------------ | --------------------------------------------------------------- |
| `shader`     | ✅            | Closed object forms validate under Azure                        |
| `modulation` | ✅            | Closed object; enumerated/typed fields                          |
| `control`    | ❌            | Azure rejects current form (e.g., `required` array constraints) |
| `tone`       | ❌            | Extensible; flexible mode (Phase 9)                             |
| `haptic`     | ❌            | Device-specific; flexible mode (Phase 9)                        |

## Architecture

### Constants

```python
# labs/v0_7_3/llm.py
AZURE_STRICT_ALLOW = {"shader", "modulation"}
AZURE_STRICT_BLOCK = {"control", "tone", "haptic"}

def supports_azure_strict(component: str) -> bool:
    return component in AZURE_STRICT_ALLOW
```

### Strict Generator (pass-through)

* Inputs: `client`, `model`, `component_name`, `subschema` (exact MCP subschema), `prompt`, `plan`.
* Behavior:

  * Log **only** schema hash + component name (no schema content).
  * Call Azure `chat.completions.create(..., response_format={"type":"json_schema","json_schema":{"name":..., "schema": subschema, "strict": True}})`.
  * Parse JSON → `dict`. On any error: return `{}` to trigger builder fallback.
* **No** schema traversal, deref, or mutation of any kind.

### Generator Routing

```python
# labs/v0_7_3/generator.py (inside per-component loop)
if supports_azure_strict(component_name):
    try:
        component_data = llm_generate_component_strict(...)
    except Exception:
        component_data = builders[component_name](prompt, subschema)
else:
    component_data = builders[component_name](prompt, subschema)

asset[component_name] = component_data
```

* After assembly, **always** validate via MCP (strict). Raise on failure.

## Tests (replace/trim to match pass-through design)

**Remove**: tests that require schema mutation (`_ensure_strict_schema*`, `$ref` resolution in Labs, control strict determinism).
**Keep/Add**:

1. **Eligibility routing**

```python
def test_strict_eligibility():
    from labs.v0_7_3.llm import supports_azure_strict
    assert supports_azure_strict("shader")
    assert supports_azure_strict("modulation")
    assert not supports_azure_strict("control")
    assert not supports_azure_strict("tone")
    assert not supports_azure_strict("haptic")
```

2. **Strict shader + modulation succeed or cleanly fallback**

```python
@pytest.mark.skipif(not AZ_CREDS, reason="Azure creds required")
def test_strict_shader_pass_or_fallback():
    # Call llm_generate_component_strict for shader with MCP subschema.
    # Accept either: non-empty dict OR {} (which then builder path is tested below).
    # No schema assertions beyond type because we do not edit schemas.
```

3. **Control uses builder** (never strict)

```python
def test_control_never_uses_strict(monkeypatch):
    from labs.v0_7_3.llm import supports_azure_strict
    assert not supports_azure_strict("control")
```

4. **End-to-end validation**

```python
@pytest.mark.skipif(not AZ_CREDS, reason="Azure creds required for strict path")
def test_generate_asset_e2e_validates():
    # generate_asset(use_llm=True, engine="azure")
    # Assert MCP validation ok, independent of whether strict path or fallback took effect.
```

5. **Determinism on strict-eligible component** (pick `shader`)

```python
@pytest.mark.skipif(not AZ_CREDS, reason="Azure creds")
def test_strict_shader_determinism():
    # Same prompt twice → identical dicts (temperature=0, seed fixed)
```

## Success Criteria

1. `shader`, `modulation` route through Azure strict when invoked; no schema mutation in Labs.
2. `control` is **never** sent to Azure strict; always builder path.
3. All generated assets **pass MCP strict validation**.
4. Deterministic outputs for strict-eligible components with same inputs.
5. Logs contain only component name and schema hash; no schema bodies or prompts.

## Implementation Checklist

* [ ] Add `AZURE_STRICT_ALLOW/BLOCK` + `supports_azure_strict()`.
* [ ] Rework `llm_generate_component_strict()` to **pure pass-through** (no `_ensure_strict_schema`, no analyzer).
* [ ] Update generator routing to honor `supports_azure_strict()` and fallback rules.
* [ ] Prune Phase 8 tests to **remove** mutation/deref assertions; add routing/determinism/E2E tests.
* [ ] Verify MCP validation passes for assets produced when strict returns content and when fallback is used.
* [ ] Update README/Phase log to document **no-mutation** policy for strict mode.

## Non-Goals

* No `$ref` resolution in Labs for Azure.
* No `additionalProperties` injection.
* No control-schema edits to appease Azure (that belongs in schema source, not Labs).

## Rationale

* Keeps Labs **schema-agnostic** and **version-isolated** per v2 SSOT.
* Eliminates previous drift introduced by local schema surgery.
* Preserves a clean migration path: when upstream schemas become Azure-strict-friendly, flip eligibility only.
