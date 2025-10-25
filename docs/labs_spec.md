---
version: v0.3.7
lastReviewed: 2025-10-25
owner: labs-core
status: stable
predecessor: v0.3.6a
---

# Synesthetic Labs — Spec v0.3.7 (Schema-Bundle Generation · 0.7.3 Lock)

> **Change lineage:**  
> Extends v0.3.6a by replacing static generator templates with schema-driven builders.  
> Generators, assemblers, and critics now consume the cached inline **MCP schema bundle** directly.  
> No normalization or post-generation mutation occurs.  
> Validation remains confirmation-only.  

---

## 1 · Scope

- Enforce schema-bound generation via live MCP descriptor (`0.7.3`).  
- Cache resolved inline schema locally; expose through `load_schema_bundle()`.  
- Route the schema bundle into the `AssetAssembler` and its component factories.  
- Replace static v0.2 templates with builders that read schema structure (`required`, `enum`, `properties`, `additionalProperties`).  
- Fallback template path gated behind feature flag `LABS_LEGACY_TEMPLATES=1`.  
- Keep MCP validation **confirmation-only**, no mutation.  
- Allow top-level metadata (`trace_id`, `deployment`, `engine`, `timestamp`) outside validation scope.  

---

## 2 · Engine Matrix

| Engine | Module | API | Binding Mode | Status | Notes |
|--------|---------|-----|--------------|--------|-------|
| `azure` | `labs/generator/external.py:AzureOpenAIGenerator` | Azure OpenAI `chat/completions` | ✅ `json_schema` | ✅ Active | Primary implementation |
| `gemini` | `labs/generator/external.py:GeminiGenerator` | Google Generative Language | ⚙️ Planned | ⚠️ Waiting for Vertex AI structured output |
| `deterministic` | `labs/generator/offline.py:DeterministicGenerator` | Local stub | ✅ | ✅ Active | CI baseline / regression harness |

---

## 3 · Defaults

| Key | Value | Notes |
|-----|--------|-------|
| Schema version | `0.7.3` | Locked globally |
| Default engine | `azure` | Override via `LABS_EXTERNAL_ENGINE` |
| Validation mode | strict | Fail-fast unless relaxed explicitly |
| MCP source | Remote schema registry | Fallback: cached bundle under `meta/schemas/` |
| Template mode | schema-driven | Legacy path only under feature flag |

---

## 4 · Environment

| Var | Purpose | Example |
|-----|----------|----------|
| `LABS_SCHEMA_VERSION` | Target schema corpus | `0.7.3` |
| `LABS_SCHEMA_RESOLUTION` | Inline/preserve/bundled | `inline` |
| `LABS_FAIL_FAST` | Strict validation toggle | `1` |
| `LABS_EXTERNAL_ENGINE` | Engine selector | `azure` |
| `LABS_LEGACY_TEMPLATES` | Enable old v0.2 static payloads | unset |
| `AZURE_OPENAI_ENDPOINT` | Azure endpoint | `https://synesthetic-aoai.openai.azure.com/` |
| `AZURE_OPENAI_API_KEY` | Resource key | `<secret>` |
| `AZURE_OPENAI_DEPLOYMENT` | Model deployment | `gpt-4o-mini` |
| `AZURE_OPENAI_API_VERSION` | API version | `2025-01-01-preview` |

Environment is pre-loaded by `_load_env_file()` before CLI startup.  
CLI flags override `.env` values.

---

## 5 · Schema Retrieval (MCP Contract)

Labs retrieves the authoritative schema from MCP before any generation or validation.  
Schema must be fetched in **`inline` resolution mode** to embed all `$ref` dependencies for strict JSON Schema compliance.

```python
schema_resp = MCPClient().fetch_schema(
    name="synesthetic-asset",
    version=os.getenv("LABS_SCHEMA_VERSION", "0.7.3"),
    resolution=os.getenv("LABS_SCHEMA_RESOLUTION", "inline"),
)
schema_bundle = schema_resp["schema"]
Path("meta/schemas/SynestheticAsset_0_7_3.json").write_text(json.dumps(schema_bundle))
```

**Resolution Modes**

| Mode       | Behavior                  | Labs Usage                    |
| ---------- | ------------------------- | ----------------------------- |
| `preserve` | Keeps `$ref` links        | ❌ Azure rejects remote `$ref` |
| `inline`   | Embeds all refs           | ✅ Required                    |
| `bundled`  | Returns root + refs array | ⚙️ Optional for offline CI    |

**Contract**

* `$id`, `name`, `version` from MCP define canonical identifiers.
* Schema bundle must not be altered or filtered.
* Equality of keys and property definitions drives validation.

---

## 6 · Generator Integration

### 6.1 · Schema Bundle Exposure

```python
# mcp_client.py
def load_schema_bundle(version="0.7.3"):
    """Return cached inline schema bundle as JSON dict."""
    path = Path(f"meta/schemas/SynestheticAsset_{version.replace('.', '_')}.json")
    if not path.exists():
        MCPClient().fetch_schema("synesthetic-asset", version=version, resolution="inline", save_to=path)
    return json.load(open(path))
```

### 6.2 · Assembler Wiring

`labs/generator/assembler.py` now accepts a `schema_bundle` argument.
Component factories access the relevant subschema via key lookup:

```python
bundle = load_schema_bundle()
assembler = AssetAssembler(schema_bundle=bundle)
asset = assembler.build(prompt)
```

Each emitted section (`shader`, `tone`, `haptic`, `control`, `modulation`, etc.) maps to its corresponding subschema node.

### 6.3 · Component Builders

Each generator component replaces static payloads with schema-driven logic:

```python
def build_tone_section(subschema):
    data = {}
    for key in subschema["required"]:
        if key in subschema["properties"]:
            prop = subschema["properties"][key]
            if "enum" in prop:
                data[key] = prop["enum"][0]
            elif "default" in prop:
                data[key] = prop["default"]
            else:
                data[key] = infer_default_for_type(prop.get("type"))
    return data
```

---

## 7 · Engine Request (Azure Schema-Bound)

```python
from openai import AzureOpenAI
import json, os

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION")
)

schema = load_schema_bundle()

resp = client.chat.completions.create(
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
    messages=[
        {"role": "system", "content": "Emit ONLY JSON conforming to the given JSON Schema."},
        {"role": "user", "content": prompt},
    ],
    response_format={
        "type": "json_schema",
        "json_schema": {"name": "SynestheticAsset_0_7_3", "schema": schema},
        "strict": True,
    },
    temperature=0,
)

asset = json.loads(resp.choices[0].message.content)
```

**Rules**

| ID                      | Requirement                                      |
| ----------------------- | ------------------------------------------------ |
| `azure-schema-bind`     | Must use `response_format.type == "json_schema"` |
| `azure-schema-source`   | Schema injected from MCP                         |
| `azure-schema-strict`   | `"strict": True` enforced                        |
| `azure-schema-validate` | Sub-object validation limited to `asset` key     |

---

## 8 · Validation (MCP)

```python
from labs.mcp.client import MCPClient

mcp = MCPClient()
result = mcp.confirm(asset, strict=True)
assert result["ok"]
```

* Validation confirms schema compliance only.
* Metadata fields outside schema ignored.
* No correction, normalization, or removal occurs.

---

## 9 · Regression Guard

`tests/test_generator_schema.py` ensures generator/critic alignment:

```python
def test_generator_schema_alignment():
    gen = GeneratorAgent(engine="azure")
    asset = gen.propose(prompt="minimal asset")
    mcp = MCPClient()
    assert mcp.confirm(asset, strict=True)["ok"]
```

Test fails if generator output or schema bundle drift occurs.

---

## 10 · Logging

Each generation logs to `meta/output/labs/external.jsonl`:

```json
{
  "timestamp": "2025-10-25T08:10:00Z",
  "engine": "azure_openai",
  "schema_id": "https://schemas.synesthetic.dev/0.7.3/synesthetic-asset.schema.json",
  "schema_version": "0.7.3",
  "schema_resolution": "inline",
  "deployment": "gpt-4o-mini",
  "trace_id": "b47a1b5c-4e7a-42ef-9efb-6bfa22f31ed8",
  "validation_status": "passed"
}
```

---

## 11 · Tests / Exit Criteria

| Area             | Requirement                                                 |
| ---------------- | ----------------------------------------------------------- |
| Env bootstrap    | Azure vars load and validate                                |
| Schema fetch     | MCP schema fetched, cached inline                           |
| Generator output | Reads from bundle, no static template                       |
| Validation       | Passes MCP strict mode                                      |
| Critic alignment | Mirrors generated structure                                 |
| No normalization | `_normalize` and `_fill_empty_sections` removed             |
| Logging          | JSONL entries include schema id/version/deployment/trace_id |
| CI               | `pytest -q` passes; `./e2e.sh` completes cleanly            |

---

## 12 · Schema Discovery Contract

| Phase      | Responsibility | Description                          |
| ---------- | -------------- | ------------------------------------ |
| Discovery  | MCP → Labs     | MCP returns authoritative descriptor |
| Generation | Labs           | Engines emit schema-bound asset      |
| Validation | Labs → MCP     | MCP confirms equality (strict)       |
| Metadata   | Labs           | Only telemetry fields exempt         |

---

### ✅ Summary

v0.3.7 defines a single-pass **schema-bundle generation loop**:

**MCP inline schema → Generator (bundle-driven emit) → MCP strict confirmation.**

* No static templates
* No normalization
* Deterministic, schema-locked behavior
* Reproducible in CI under `0.7.3`
