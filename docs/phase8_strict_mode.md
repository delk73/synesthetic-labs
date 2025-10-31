**Prompt ID:** phase8_strict_mode_minimal  
**Purpose:** Implement hard, fallback-free Phase 8 strict-mode LLM generation in Synesthetic Labs (v0.7.3).  
**Audience:** Labs developer (strict pipeline only).  

---

### Prompt

Implement **Phase 8 — Strict Mode LLM Generation (Hard Mode)** for Synesthetic Labs v0.7.3.  
Target: deterministic generation of one component (`shader` or `control`) through Azure OpenAI `json_schema` strict mode.  
Remove all fallback logic, retries, or local schema edits.

---

### Requirements

**1. MCP Authority Only**
- Only TCP transport.  
- No STDIO, socket, or local cache.  
- On any MCP error → raise `MCPUnavailableError`.

**2. Schema Integrity**
- Fetch inline bundle from MCP.  
- Never mutate `$id`, `$schema`, `required`, or `additionalProperties`.  
- Pass subschema exactly as received.

**3. Strict Generation Path**
- Function `generate_strict_component()` only.  
- Azure params: `temperature=0`, `seed=0`, `max_tokens=2048`.  
- `response_format={"type":"json_schema","json_schema":{"strict":true}}`.  
- Parse single JSON response; if parse fails → raise `StrictGenerationError`.  
- **No builder, no fallback, no retry.**

**4. Validation**
- After generation, validate with MCP/TCP.  
- On validation failure → raise `MCPValidationError`.

**5. Telemetry**
- Log only: `component`, `schema_sha256`, `status`.  
- No schema or prompt body logging.

---

### Implementation Outline

```python
class MCPUnavailableError(Exception): pass
class StrictGenerationError(Exception): pass

def mcp_fetch_schema(client, version):
    bundle = client.fetch_inline_bundle(version)
    if not isinstance(bundle, dict): raise MCPUnavailableError
    return bundle

def generate_strict_component(azure, model, component, subschema, prompt):
    h = sha256(json.dumps(subschema, sort_keys=True).encode()).hexdigest()
    log.info("strict.start %s sha=%s", component, h)
    resp = azure.chat.completions.create(
        model=model,
        temperature=0,
        seed=0,
        response_format={"type":"json_schema","json_schema":{"name":component,"schema":subschema,"strict":True}},
        messages=[{"role":"user","content":prompt}],
        max_tokens=2048,
    )
    try:
        return json.loads(resp.choices[0].message.content)
    except Exception as e:
        raise StrictGenerationError(f"invalid JSON: {e}")
```

```python
def generate_asset_strict(client, azure, model, version, prompt, component):
    subschema = mcp_fetch_schema(client, version)["components"][component]
    data = generate_strict_component(azure, model, component, subschema, prompt)
    client.validate_asset({component: data}, version)
    return {component: data}
```

---

### Tests / Assertions

| Case                  | Expectation               |
| --------------------- | ------------------------- |
| MCP offline           | `MCPUnavailableError`     |
| Azure invalid JSON    | `StrictGenerationError`   |
| Valid strict path     | deterministic dict output |
| Schema mutation check | subschema hash unchanged  |
| No fallback           | no builder invoked        |

---

### Acceptance Criteria

* Deterministic strict generation only.
* No fallback or schema mutation.
* Validation strictly via MCP/TCP.
* Fail-fast behavior; developer-grade reproducibility.

---

### Implementation Notes · 2025-10-29

- `labs/mcp/client.py` now enforces TCP-only operation. Any schema or validation failure raises `MCPUnavailableError`; the legacy `mcp.core` fallback path has been removed in favor of real transport errors.
- `labs/mcp_stdio.py` was collapsed to a TCP shim, reflecting the removal of STDIO/Unix socket adapters from the runtime surface.
- `labs/v0_7_3/llm.py` exposes `generate_strict_component()` plus `StrictGenerationError`, providing a deterministic strict-mode wrapper that logs only component, schema hash, and status.
- `labs/v0_7_3/generator.py` routes `use_llm=True` + `engine="azure"` through `_generate_strict_with_azure()`; there is no builder fallback, so strict-mode failures bubble up as `StrictGenerationError` or `MCPValidationError`.

> TODO: Reintroduce alternate MCP transports (socket/stdio) once a formal proposal and test strategy are in place.

#### Manual Verification Checklist

1. Export Azure credentials: `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`, and optionally `AZURE_OPENAI_API_VERSION`.
2. Ensure the MCP TCP server is reachable (`make mcp-check`).
3. Generate a strict component directly:

    ```bash
    make generate-strict-component COMPONENT=shader P="Minimal control shader"
    ```

    The helper wraps `python -m labs.v0_7_3.strict_cli`, which:
    - Fetches the inline schema via TCP MCP.
    - Builds the component-specific subschema with `SchemaAnalyzer`.
    - Calls `AzureOpenAI.chat.completions.create` with `temperature=0.0`, `seed=0`, and `response_format=json_schema`.
    - Validates the component-wrapped asset via `MCPClient.confirm(...)`.
4. Swap `COMPONENT` for `control` or `modulation` to exercise other Phase 8 targets.
5. Use `-o component.json` to persist the payload for inspection.

```
