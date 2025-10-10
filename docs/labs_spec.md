---
version: v0.3.6a
lastReviewed: 2025-10-10
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
| **v0.3.6a** | 2025-10-10 | Azure integration | Adds Azure OpenAI engine and environment contract |

---

## 1 · Scope

v0.3.6a resolves the semantic, provenance, and validation gaps identified in v0.3.5a  
**and** introduces a second live generator backend: **Azure OpenAI**.

Focus areas:
- Completing Gemini schema binding and parsing to canonical contract.  
- Adding full Azure OpenAI `chat.completions` structured-output parity.  
- Restoring enriched provenance for schema ≥ 0.7.4.  
- Re-enabling `invoke_mcp()` lifecycle validation.  
- Ensuring both backends pass strict validation unassisted.

---

## 2 · Engine Matrix

| Engine | Module | API | JSON Mode | Cost | Notes |
|---------|---------|-----|------------|------|-------|
| `gemini` | `labs/generator/external.py:GeminiGenerator` | Google Generative Language | ✅ | Low | Legacy baseline |
| `azure` | `labs/generator/external.py:AzureOpenAIGenerator` | Azure OpenAI `chat/completions` | ✅ | Low | Preferred structured-output path |
| `deterministic` | `labs/generator/offline.py:DeterministicGenerator` | Local stub | ✅ | n/a | For CI / offline |

---

## 3 · Defaults

| Key | Value | Notes |
|-----|--------|-------|
| Schema version | `0.7.3` | 0.7.4+ for enriched provenance |
| Gemini model | `gemini-2.0-flash` | |
| Azure deployment | `gpt-4o-mini` | |
| Validation mode | strict (default) | CLI or `LABS_FAIL_FAST` toggles relaxed |
| Config precedence | CLI → env → default | |
| MCP schema source | Remote (strict) / local (fallback) | |

---

## 4 · Environment

### 4.1 Shared Variables

| Var | Purpose |
|-----|----------|
| `LABS_SCHEMA_VERSION` | Target schema corpus (default `"0.7.3"`) |
| `LABS_FAIL_FAST` | Enables strict validation when `true` or `1` |
| `LABS_EXTERNAL_ENGINE` | Engine override (`gemini`, `azure`, `deterministic`) |
| `SYN_SCHEMAS_DIR` | Fallback local schema path |

### 4.2 Gemini Variables

| Var | Purpose |
|-----|----------|
| `LABS_EXTERNAL_LIVE` | Enables live Gemini generation |
| `GEMINI_MODEL` | Gemini model identifier |
| `GEMINI_API_KEY` | API key for Gemini |

### 4.3 Azure Variables

| Var | Purpose | Example |
|-----|----------|----------|
| `AZURE_OPENAI_ENDPOINT` | Azure resource endpoint | `https://synesthetic-aoai.openai.azure.com/` |
| `AZURE_OPENAI_API_KEY` | Resource key | `<secret>` |
| `AZURE_OPENAI_DEPLOYMENT` | Model deployment name | `gpt-4o-mini` |
| `AZURE_OPENAI_API_VERSION` | API version for the client | `2025-01-01-preview` |

All variables load via `_load_env_file()` and merge into `os.environ`.

---

## 5 · Generator Contract

```python
def generate_asset(
    prompt: str,
    schema_version: str = "0.7.3",
    engine: str = "gemini",
    strict: bool = True
) -> dict:
    """Return a schema-compliant SynestheticAsset with provenance and validation."""
```

CLI usage:

```bash
labs generate "prompt" --engine azure --schema-version 0.7.3 [--strict|--relaxed]
```

---

## 6 · Schema Retrieval (MCP)

All schemas must be fetched through MCP prior to normalization or validation.

```python
from mcp.core import get_schema
schema_resp = get_schema("synesthetic-asset")
schema = schema_resp["schema"]
```

On failure → log `failure_mcp_unavailable`; abort in live mode.
Deterministic mode may use local `meta/schemas/` stubs.

---

## 7 · Engine Request Contracts

### 7.1 Gemini Request

```json
{
  "contents": [
    {"role": "user", "parts": [{"text": "<prompt>"}]}
  ],
  "generation_config": {
    "response_mime_type": "application/json",
    "response_schema": {
      "jsonSchema": {
        "$ref": "https://schemas.synesthetic.dev/0.7.3/synesthetic-asset.schema.json"
      }
    }
  },
  "model": "gemini-2.0-flash"
}
```

### 7.2 Azure Request

```python
from openai import AzureOpenAI
import os, json

client = AzureOpenAI(
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
)

response = client.chat.completions.create(
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    messages=[
        {"role": "system", "content": "You are a schema-bound generator."},
        {"role": "user", "content": "<prompt>"}
    ],
    response_format={"type": "json_object"}
)

asset = json.loads(response.choices[0].message.content)
```

Both engines must emit structured JSON that validates under the active schema.

---

## 8 · Normalization & Semantic Filling

| Section     | Fallback Source                   |
| ----------- | --------------------------------- |
| `shader`    | `AssetAssembler.default_shader()` |
| `tone`      | `AssetAssembler.default_tone()`   |
| `haptic`    | `AssetAssembler.default_haptic()` |
| `control`   | `_DEFAULT_CONTROL_PARAMETERS`     |
| `meta_info` | Static tags / schema examples     |

Enriched (≥ 0.7.4) assets must append provenance.

---

## 9 · Provenance Schema

| Field              | Description           | Example                    |
| ------------------ | --------------------- | -------------------------- |
| `engine`           | Generator engine      | `gemini` or `azure_openai` |
| `endpoint`         | Service endpoint      | Gemini or Azure URL        |
| `deployment`       | Model / deployment ID | `gpt-4o-mini`              |
| `trace_id`         | UUID                  | `"b85b9e..."`              |
| `api_version`      | API version string    | `"2025-01-01-preview"`     |
| `input_parameters` | Echoed parameters     | `{...}`                    |

Example (Azure):

```json
{
  "engine": "azure_openai",
  "endpoint": "https://synesthetic-aoai.openai.azure.com/",
  "deployment": "gpt-4o-mini",
  "trace_id": "dfe12e0f-fc93-4e0a-8f02-bf9b8d7c126a",
  "api_version": "2025-01-01-preview",
  "input_parameters": {}
}
```

---

## 10 · CLI Lifecycle

1. **Preflight** — Load `.env`, resolve engine/schema/mode, generate `trace_id`.
2. **Schema Pull** — Fetch schema via MCP.
3. **Dispatch** — Call selected generator (Gemini or Azure).
4. **Normalize** — Fill empty fields, inject provenance.
5. **Validate** — Use `invoke_mcp()` with strict/relaxed handling.
6. **Persist** — Write structured log entries with validation metadata.

---

## 11 · Validation Rules

* `$schema` must match resolved version.
* Structural fields may not be empty.
* `meta_info` must include at least one tag.
* Enriched schemas (≥ 0.7.4) must contain provenance keys.

---

## 12 · Error Classes

| Code               | Condition                | Action       |
| ------------------ | ------------------------ | ------------ |
| `auth_error`       | 401 / 403                | stop         |
| `bad_request`      | 400 invalid body         | stop         |
| `network_error`    | timeout                  | retry ≤ 3    |
| `server_error`     | 5xx                      | retry ≤ 3    |
| `bad_response`     | malformed / empty output | stop         |
| `validation_error` | strict validation failed | stop / relax |
| `mcp_unavailable`  | MCP offline              | stop         |

---

## 13 · Logging

Every generation run emits structured JSONL to:

* `meta/output/labs/external.jsonl`
* `meta/output/labs/generator.jsonl`

Example:

```json
{
  "timestamp": "2025-10-10T08:15:32Z",
  "engine": "azure_openai",
  "schema_version": "0.7.3",
  "trace_id": "7a235ea3-1b5b-4bb4-8a65-3f98c3d7d215",
  "validation_status": "passed",
  "schema_binding": true,
  "taxonomy": "success"
}
```

---

## 14 · Tests / Exit Criteria

| Area                  | Requirement                               |
| --------------------- | ----------------------------------------- |
| Env bootstrap         | Azure vars recognized and loaded          |
| Schema retrieval      | MCP returns valid dict                    |
| Gemini / Azure        | Return valid JSON objects                 |
| Response parsing      | Canonical extraction path only            |
| Fallback filling      | Empty sections replaced deterministically |
| Provenance            | Complete and correct                      |
| CLI validation        | `invoke_mcp()` works in both modes        |
| MCP strict validation | Passes for schema 0.7.3                   |
| CI                    | `pytest -q` green                         |

---

## 15 · Non-Goals

* No schema version bump beyond 0.7.4.
* No cross-engine fallback beyond azure/gemini.
* No new operator or transport types.

---

## 16 · Version Lineage Diagram

```
v0.3.4 → v0.3.5 → v0.3.5a → v0.3.6 → v0.3.6a
(core)   (transport) (audit)   (semantic)  (azure)
 |------------ stabilized Gemini transport -------------|
 |---------------- semantic + validation integrity ----------------|
 |-------------------- Azure parity + multi-engine --------------------|
```

---

### ✅ Summary

v0.3.6a finalizes the **semantic alignment** and introduces **Azure OpenAI parity**.
Both Gemini and Azure paths now share a unified schema-bound generator contract, deterministic
normalization, and MCP-based validation pipeline.

This release is the stable foundation for **v0.3.7** — provenance-rich multi-backend schema evolution.