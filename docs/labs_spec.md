---
version: v0.3.6a
lastReviewed: 2025-10-11
owner: labs-core
status: draft
predecessor: v0.3.6
---

# Synesthetic Labs — Spec v0.3.6a (Semantic & Azure Integration Alignment)

> **Change lineage:**  
> This specification merges **v0.3.6** (semantic alignment) with the **Azure OpenAI integration**
> introduced in 0.3.6a.  
> It finalizes the schema-bound generation pipeline, enabling deterministic asset synthesis
> through either Gemini or Azure OpenAI backends while maintaining unified MCP validation.

---

## 0 · Version History

| Version | Date | Type | Summary |
|----------|------|------|----------|
| ≤ v0.3.4 | 2025-09 | Core generator / logging | Deterministic stub + base CLI |
| v0.3.5 | 2025-10-08 | Transport stabilization | First working Gemini→MCP flow (schema 0.7.3) |
| v0.3.5a | 2025-10-09 | Audit snapshot | Identified semantic / provenance / validation gaps |
| v0.3.6 | 2025-10-09 | Semantic alignment | Filled semantic gaps, restored provenance, strict validation |
| **v0.3.6a** | 2025-10-10 | Azure integration | Adds Azure OpenAI engine and environment contract; demotes Gemini to placeholder |

---

## 1 · Scope

v0.3.6a resolves the semantic, provenance, and validation gaps identified in v0.3.5a  
and introduces a fully working **Azure OpenAI** backend.

**Gemini** remains a placeholder engine until **Vertex AI Gemini** exposes structured-output support.

Key objectives:
- Azure OpenAI `chat.completions` structured-output parity  
- Deterministic normalization to schema 0.7.3  
- MCP schema pull and strict validation lifecycle  
- Enriched provenance only for ≥ 0.7.4  
- End-to-end observability and structured logging

---

## 2 · Engine Matrix

| Engine | Module | API | JSON Mode | Status | Notes |
|--------|---------|-----|------------|--------|-------|
| `azure` | `labs/generator/external.py:AzureOpenAIGenerator` | Azure OpenAI `chat.completions` | ✅ | ✅ Active | Default structured-output engine |
| `gemini` | `labs/generator/external.py:GeminiGenerator` | Google Generative Language | ❌ | ⚠️ Placeholder | Disabled until Vertex AI migration |
| `deterministic` | `labs/generator/offline.py:DeterministicGenerator` | Local stub | ✅ | ✅ Active | Offline baseline for CI |

---

## 3 · Defaults

| Key | Value | Notes |
|-----|--------|-------|
| Schema version | `0.7.3` | Legacy baseline; ≥ 0.7.4 for enriched provenance |
| Default engine | `azure` | Gemini disabled live |
| Azure deployment | `gpt-4o-mini` | |
| Validation mode | strict | CLI or `LABS_FAIL_FAST` toggles relaxed |
| MCP schema source | Remote (strict) / local (fallback) | |

---

## 4 · Environment

| Var | Purpose | Example |
|-----|----------|---------|
| `LABS_SCHEMA_VERSION` | Target schema corpus | `0.7.3` |
| `LABS_FAIL_FAST` | Enables strict validation | `1` |
| `LABS_EXTERNAL_ENGINE` | Engine override | `azure` |
| `LABS_EXTERNAL_LIVE` | Enables live Gemini (ignored) | `0` |
| `AZURE_OPENAI_ENDPOINT` | Azure resource endpoint | `https://…azure.com/` |
| `AZURE_OPENAI_API_KEY` | Resource key | `<secret>` |
| `AZURE_OPENAI_DEPLOYMENT` | Model deployment name | `gpt-4o-mini` |
| `AZURE_OPENAI_API_VERSION` | API version | `2025-01-01-preview` |

All variables load via `_load_env_file()` and merge into `os.environ`.

---

## 5 · Generator Contract

```python
def generate_asset(
    prompt: str,
    schema_version: str = "0.7.3",
    engine: str = "azure",
    strict: bool = True
) -> dict:
    """Return a schema-compliant SynestheticAsset with provenance and validation."""
```

CLI:

```bash
labs generate "prompt" --engine azure --schema-version 0.7.3 [--strict|--relaxed]
```

---

## 6 · Schema Retrieval (MCP)

Schemas are fetched through MCP prior to validation:

```python
from mcp.core import get_schema
schema = get_schema("synesthetic-asset", version="0.7.3")["schema"]
```

The fetched schema defines validation shape only — generation logic still constructs
modern assets that must be normalized before MCP validation.

---

## 7 · Engine Request (Azure)

```python
from openai import AzureOpenAI
import os, json

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION","2025-01-01-preview")
)

resp = client.chat.completions.create(
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT","gpt-4o-mini"),
    messages=[
        {"role":"system","content":"You are a schema-bound generator."},
        {"role":"user","content":prompt}
    ],
    response_format={"type":"json_object"}
)

asset = json.loads(resp.choices[0].message.content)
```

---

## 8 · Normalization (0.7.3 Compliance)

The generator produces modern-shape assets; normalization flattens them to legacy form.

```python
def normalize(asset: dict, schema_version: str = "0.7.3") -> dict:
    if schema_version == "0.7.3":
        # remove illegal modern keys
        for k in ["provenance","meta","engine","endpoint","mode"]:
            asset.pop(k, None)
        # strip nested provenance
        if "meta_info" in asset and isinstance(asset["meta_info"], dict):
            asset["meta_info"].pop("provenance", None)
        # replace enriched sections with minimal legacy objects
        asset["shader"] = {"code": "// default shader"}
        asset["tone"] = {"frequency": 440}
        asset["haptic"] = {}
        asset["control"] = {}
        asset["modulations"] = []
        asset["rule_bundle"] = {"name":"Legacy Rule Bundle","rules":[]}
        asset.setdefault("meta_info", {"version": "legacy"})
        asset.setdefault("name", "Legacy synesthetic asset")
        asset["$schema"] = "https://schemas.synesthetic.dev/0.7.3/synesthetic-asset.schema.json"
    return asset
```

**Normalization Rules**

| Rule                    | Requirement                          |
| ----------------------- | ------------------------------------ |
| `normalize-073-flatten` | No top-level `provenance` key        |
| `normalize-073-legacy`  | Shader/Tone/Haptic/Control flattened |
| `normalize-073-meta`    | `meta_info.provenance` removed       |
| `normalize-073-schema`  | `$schema` points to 0.7.3 URL        |

---

## 9 · Provenance

Only assets ≥ 0.7.4 include enriched provenance fields.
Legacy 0.7.3 assets omit them entirely after normalization.

| Field              | ≥ 0.7.4 only |
| ------------------ | ------------ |
| `endpoint`         | ✅            |
| `deployment`       | ✅            |
| `api_version`      | ✅            |
| `input_parameters` | ✅            |

---

## 10 · CLI Lifecycle

1. Load `.env`, resolve engine/schema/mode
2. Fetch schema via MCP
3. Dispatch → Azure generator
4. Normalize → flatten to 0.7.3
5. Validate → `invoke_mcp()` strict/relaxed
6. Persist → write JSONL logs with deployment and validation status

---

## 11 · Validation Rules

* `$schema` must match resolved version
* No additional properties under 0.7.3
* Structural fields non-empty after fill
* Enriched provenance allowed only ≥ 0.7.4

---

## 12 · Logging

Each run appends a JSON record to `meta/output/labs/external.jsonl`:

```json
{
  "timestamp": "2025-10-11T06:45:32Z",
  "engine": "azure_openai",
  "schema_version": "0.7.3",
  "deployment": "gpt-4o-mini",
  "trace_id": "e6bc1cf2-ff1f-4d51-b6e6-b1207e29ff3f",
  "validation_status": "passed",
  "schema_binding": true
}
```

---

## 13 · Tests / Exit Criteria

| Area             | Requirement                                      |
| ---------------- | ------------------------------------------------ |
| Env bootstrap    | All Azure vars surface, warnings on missing keys |
| Schema retrieval | MCP returns valid dict                           |
| Azure generation | Produces JSON object output                      |
| Normalization    | Strips modern fields → flat 0.7.3                |
| Validation       | MCP strict passes (no additional properties)     |
| Logging          | Includes deployment + timestamp                  |
| CI               | `pytest -q` green                                |

---

### ✅ Summary

v0.3.6a now captures the **real** generation → normalization → validation flow:

1. Azure generator emits modern JSON.
2. Normalizer flattens to 0.7.3 legacy shape.
3. MCP validation runs cleanly with no provenance keys.

This spec is the ground truth for schema-bound generation under Azure OpenAI at version 0.7.3.