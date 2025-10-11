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
> schema (fetched from MCP at runtime).

---

## 1 · Scope

- Enforce schema-bound generation via the model’s structured-output interface.  
- Remove all normalization logic.  
- Keep MCP validation as a confirmation step only.  
- Support multiple schema versions (`0.7.3`, `0.7.4+`) through the same binding pipeline.

---

## 2 · Engine Matrix

| Engine | Module | API | Binding Mode | Status | Notes |
|--------|---------|-----|--------------|--------|-------|
| `azure` | `labs/generator/external.py:AzureOpenAIGenerator` | Azure OpenAI `chat/completions` | ✅ `json_schema` | ✅ Active | Reference engine |
| `gemini` | `labs/generator/external.py:GeminiGenerator` | Google Generative Language | ❌ | ⚠️ Placeholder | Disabled until Vertex AI supports schema binding |
| `deterministic` | `labs/generator/offline.py:DeterministicGenerator` | Local stub | ✅ | ✅ Active | CI baseline |

---

## 3 · Defaults

| Key | Value | Notes |
|-----|--------|-------|
| Schema version | `0.7.3` | Default; switchable to ≥ `0.7.4` |
| Default engine | `azure` | |
| Validation mode | strict | `--relaxed` or `LABS_FAIL_FAST=0` for non-fatal warnings |
| MCP source | Remote authoritative schema service | |

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
                         version=os.getenv("LABS_SCHEMA_VERSION","0.7.3"))
schema = schema_resp["schema"]
schema_id = schema_resp["id"]
```

The retrieved JSON Schema is authoritative for both generation and validation.

---

## 6 · Engine Request (Azure Schema-Bound)

```python
from openai import AzureOpenAI
import os, json
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION","2025-01-01-preview")
)

schema = get_schema("synesthetic-asset", version="0.7.3")["schema"]

resp = client.chat.completions.create(
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT","gpt-4o-mini"),
    messages=[
        {"role":"system","content":"Emit ONLY JSON conforming to the given JSON Schema."},
        {"role":"user","content":prompt}
    ],
    response_format={
        "type":"json_schema",
        "json_schema":{
            "name":"SynestheticAsset_0_7_3",
            "schema":schema,
            "strict":True
        }
    },
    temperature=0
)

asset = json.loads(resp.choices[0].message.content)
```

**Rules**

| ID                    | Requirement                             |
| --------------------- | --------------------------------------- |
| `azure-schema-bind`   | `response_format.type == "json_schema"` |
| `azure-schema-source` | Schema object comes from live MCP fetch |
| `azure-schema-strict` | `"strict": True` enforced               |
| `azure-schema-trace`  | Log must include schema id + version    |

---

## 7 · Validation (MCP)

Validation confirms—not corrects—the output.

```python
from labs.mcp.validate import invoke_mcp
result = invoke_mcp(asset, strict=True)
assert result["ok"]
```

No normalization or field rewriting is permitted.

---

## 8 · Logging

Each generation run appends a line to `meta/output/labs/external.jsonl`:

```json
{
  "timestamp": "2025-10-11T08:10:00Z",
  "engine": "azure_openai",
  "schema_version": "0.7.3",
  "schema_id": "mcp:synesthetic-asset@0.7.3",
  "deployment": "gpt-4o-mini",
  "trace_id": "2a1c4f4e-51ad-4a1c-b8d2-67e65bfcf74e",
  "validation_status": "passed"
}
```

---

## 9 · Tests / Exit Criteria

| Area              | Requirement                                                  |
| ----------------- | ------------------------------------------------------------ |
| Env bootstrap     | All Azure vars load, warnings shown if missing               |
| MCP fetch         | Schema returned, cached, id logged                           |
| Azure generation  | Uses `response_format.type == "json_schema"`                 |
| Schema compliance | MCP validation `ok == True`                                  |
| No normalization  | No calls to any `_normalize`, `_fill`, or “fallback” helpers |
| Logging           | JSONL entries include `schema_id` and `schema_version`       |
| CI                | `pytest -q` green                                            |

---

### ✅ Summary

v0.3.6a defines a **single-pass, schema-bound generation pipeline**:

**MCP Schema → Azure chat.completions (json_schema) → MCP validate.**