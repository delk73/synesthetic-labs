---
version: v0.3.6a
lastReviewed: 2025-10-11
owner: labs-core
status: stable
predecessor: v0.3.6
---

# Synesthetic Labs — Spec v0.3.6a (True Schema-Bound Generation)

> **Change lineage:**  
> This release replaces the old *generate → normalize → validate* pattern with a single,
> strictly schema-bound generation contract.  
> Every engine now emits assets that are *born compliant* with the active SynestheticAsset
> schema (fetched live from MCP).

---

## 1 · Scope

- Enforce schema-bound generation via the model’s structured-output interface.  
- Remove all normalization logic.  
- Keep MCP validation as a **confirmation-only** step.  
- Support multiple schema versions (`0.7.3`, `0.7.4+`) through the same binding pipeline.  
- Preserve top-level metadata while validating inner schema objects only.

---

## 2 · Engine Matrix

| Engine | Module | API | Binding Mode | Status | Notes |
|--------|---------|-----|--------------|--------|-------|
| `azure` | `labs/generator/external.py:AzureOpenAIGenerator` | Azure OpenAI `chat/completions` | ✅ `json_schema` | ✅ Active | Reference implementation |
| `gemini` | `labs/generator/external.py:GeminiGenerator` | Google Generative Language | ❌ | ⚠️ Placeholder | Disabled until Vertex AI supports structured output |
| `deterministic` | `labs/generator/offline.py:DeterministicGenerator` | Local stub | ✅ | ✅ Active | CI baseline |

---

## 3 · Defaults

| Key | Value | Notes |
|-----|--------|-------|
| Schema version | `0.7.3` | Switchable to ≥ `0.7.4` |
| Default engine | `azure` | |
| Validation mode | strict | Controlled by `LABS_FAIL_FAST` or CLI flags |
| MCP source | Remote schema registry | Fallback to local `meta/schemas` |

---

## 4 · Environment

| Var | Purpose | Example |
|-----|----------|---------|
| `LABS_SCHEMA_VERSION` | Target schema corpus | `0.7.3` |
| `LABS_FAIL_FAST` | Strict / relaxed validation toggle | `1` |
| `LABS_EXTERNAL_ENGINE` | Engine selector | `azure` |
| `AZURE_OPENAI_ENDPOINT` | Azure resource endpoint | `https://synesthetic-aoai.openai.azure.com/` |
| `AZURE_OPENAI_API_KEY` | Resource key | `<secret>` |
| `AZURE_OPENAI_DEPLOYMENT` | Model deployment | `gpt-4o-mini` |
| `AZURE_OPENAI_API_VERSION` | API version | `2025-01-01-preview` |

All variables load through `_load_env_file()` at CLI startup.

---

## 5 · Schema Retrieval (MCP)

```python
from mcp.core import get_schema
schema_resp = get_schema("synesthetic-asset",
                         version=os.getenv("LABS_SCHEMA_VERSION", "0.7.3"))
schema = schema_resp["schema"]
schema_id = schema_resp["id"]
```

Schemas are cached in `_cached_schema_descriptor` for reuse across engines.

---

## 6 · Engine Request (Azure Schema-Bound)

```python
from openai import AzureOpenAI
import os, json

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
)

schema = get_schema("synesthetic-asset", version="0.7.3")["schema"]

resp = client.chat.completions.create(
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
    messages=[
        {"role": "system", "content": "Emit ONLY JSON conforming to the given JSON Schema."},
        {"role": "user", "content": prompt}
    ],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "SynestheticAsset_0_7_3",
            "schema": schema
        },
        "strict": True
    },
    temperature=0
)

raw = json.loads(resp.choices[0].message.content)
```

---

## 7 · Validation (MCP)

Validation confirms the schema match without mutation:

```python
from labs.mcp.validate import invoke_mcp
result = invoke_mcp(asset, strict=True)
assert result["ok"]
```

Partial validation may be applied to sub-objects only (e.g., `asset` key) while retaining
metadata such as `trace_id`, `deployment`, or `engine`.

---

## 8 · Logging

Each generation run appends a record to `meta/output/labs/external.jsonl`:

```json
{
  "timestamp": "2025-10-11T08:10:00Z",
  "engine": "azure_openai",
  "schema_id": "https://schemas.synesthetic.dev/0.7.3/synesthetic-asset.schema.json",
  "schema_version": "0.7.3",
  "deployment": "gpt-4o-mini",
  "trace_id": "2a1c4f4e-51ad-4a1c-b8d2-67e65bfcf74e",
  "validation_status": "passed"
}
```

---

## 9 · Tests / Exit Criteria

| Area             | Requirement                                          |
| ---------------- | ---------------------------------------------------- |
| Env bootstrap    | Azure vars loaded and verified                       |
| Schema fetch     | MCP schema retrieved and cached                      |
| Azure generation | Uses `response_format.type == "json_schema"`         |
| Parsing          | Deterministic `json.loads`, no regex                 |
| Validation       | Strict MCP confirmation passes                       |
| No normalization | No `_normalize` or `_fill_empty_sections` references |
| Logging          | Includes schema id, version, deployment, trace id    |
| CI               | `pytest -q` passes                                   |

---

### ✅ Summary

v0.3.6a now defines a **single-pass schema-bound generation loop**:

**MCP schema → Azure Chat Completions (json_schema) → Sub-object validation → MCP confirmation.**

No normalization, no stripping, no fallback — schema compliance is guaranteed at generation time.