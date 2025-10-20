---
version: v0.3.6a
lastReviewed: 2025-10-11
owner: labs-core
status: stable
predecessor: v0.3.6
---

# Synesthetic Labs — Spec v0.3.6a (Schema-Bound Generation · 0.7.3 Lock)

> **Change lineage:**  
> Replaces the legacy *generate → normalize → validate* pattern with a single,
> schema-bound generation contract.  
> Engines emit assets *born compliant* with the active SynestheticAsset schema
> (fetched live from MCP).  
> Validation confirms compliance only — no mutation, normalization, or stripping.

---

## 1 · Scope

- Enforce schema-bound generation via model’s structured-output interface  
- Remove all normalization logic  
- Keep MCP validation **confirmation-only**  
- Fix all engines to the SynestheticAsset `0.7.3` schema  
- Allow top-level metadata (`trace_id`, `deployment`, `engine`, `timestamp`) to remain outside validation scope  

---

## 2 · Engine Matrix

| Engine | Module | API | Binding Mode | Status | Notes |
|--------|---------|-----|--------------|--------|-------|
| `azure` | `labs/generator/external.py:AzureOpenAIGenerator` | Azure OpenAI `chat/completions` | ✅ `json_schema` | ✅ Active | Reference implementation |
| `gemini` | `labs/generator/external.py:GeminiGenerator` | Google Generative Language | ❌ | ⚠️ Placeholder | Disabled until Vertex AI supports schema binding |
| `deterministic` | `labs/generator/offline.py:DeterministicGenerator` | Local stub | ✅ | ✅ Active | CI baseline |

---

## 3 · Defaults

| Key | Value | Notes |
|-----|--------|-------|
| Schema version | `0.7.3` | Locked for all engines |
| Default engine | `azure` | Overrides mock unless `LABS_EXTERNAL_ENGINE` explicitly set |
| Validation mode | strict | Controlled by `LABS_FAIL_FAST` / CLI flags |
| MCP source | Remote schema registry | Fallback: local `meta/schemas` |

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

Loaded by `_load_env_file()` before CLI startup.  
If CLI `--engine` flag is omitted, `.env` takes precedence.

---

## 5 · Schema Retrieval (MCP)

```python
from mcp.core import get_schema
schema_resp = get_schema(
    "synesthetic-asset",
    version=os.getenv("LABS_SCHEMA_VERSION", "0.7.3"),
)
schema_name = schema_resp["name"]
schema_version = schema_resp["version"]
schema_path = schema_resp["path"]
schema = schema_resp["schema"]
schema_id = schema.get("$id")
```

Schema descriptors are cached in `_cached_schema_descriptor`
for reuse across generation and validation.

The MCP response is the source of truth for schema metadata. Clients must rely on
the returned `schema_name`, `schema_version`, and `schema_path`, comparing the
reported version against the requested `LABS_SCHEMA_VERSION` to surface drift.

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

asset = json.loads(resp.choices[0].message.content)
```

**Rules**

| ID                      | Requirement                                        |
| ----------------------- | -------------------------------------------------- |
| `azure-schema-bind`     | `response_format.type == "json_schema"`            |
| `azure-schema-source`   | Schema injected directly from MCP                  |
| `azure-schema-strict`   | `"strict": True` enforced                          |
| `azure-schema-validate` | Sub-object validation allowed for `asset` key only |

---

## 7 · Validation (MCP)

```python
from labs.mcp.client import MCPClient

mcp = MCPClient()
result = mcp.confirm(asset, strict=True)
assert result["ok"]
```

* Validation confirms schema compliance only.
* Top-level telemetry fields (`trace_id`, `timestamp`, `deployment`, etc.)
  are ignored during validation scope.
* No mutation or normalization permitted.

---

## 8 · Logging

Each run appends to `meta/output/labs/external.jsonl`:

```json
{
  "timestamp": "2025-10-11T08:10:00Z",
  "engine": "azure_openai",
  "schema_id": "https://schemas.synesthetic.dev/0.7.3/synesthetic-asset.schema.json",
  "schema_version": "0.7.3",
  "schema_resolution": "preserve",
  "deployment": "gpt-4o-mini",
  "trace_id": "2a1c4f4e-51ad-4a1c-b8d2-67e65bfcf74e",
  "validation_status": "passed"
}
```

---

## 9 · Tests / Exit Criteria

| Area             | Requirement                                                 |
| ---------------- | ----------------------------------------------------------- |
| Env bootstrap    | Azure vars load and validate                                |
| Schema fetch     | MCP schema fetched and cached                               |
| Azure generation | Uses `json_schema` response_format                          |
| Parsing          | Strict `json.loads` only                                    |
| Validation       | Passes MCP strict mode (no correction)                      |
| No normalization | No `_normalize`, `_fill_empty_sections`, or stripping       |
| Logging          | JSONL entries include schema id/version/deployment/trace_id |
| CI               | `pytest -q` passes                                          |

---

### ✅ Summary

v0.3.6a defines a **single-pass, schema-bound generation loop**:

**MCP Schema → Azure Chat Completions (json_schema) → Sub-object validation → MCP confirmation.**

Normalization removed.
`.env` overrides respected.
Mocks never override live engines.

```

---

✅ **Changes applied vs prior draft**
1. Clarified `.env` precedence for `LABS_EXTERNAL_ENGINE`.  
2. Explicitly allowed top-level metadata outside validation scope.  
3. Removed any fallback/normalization ambiguity.  
4. Added sub-object validation allowance (for `asset` key only).  
