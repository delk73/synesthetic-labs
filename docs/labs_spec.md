---
version: v0.3.6
lastReviewed: 2025-10-09
owner: labs-core
status: draft
predecessor: v0.3.5
---

# Synesthetic Labs — Spec v0.3.6 (Semantic & Validation Alignment)

> **Change lineage:**  
> This specification evolves directly from **v0.3.5** (schema-bound Gemini integration).  
> It implements the corrective actions and recommendations documented in  
> **Synesthetic Labs State Report (v0.3.5a)**, addressing semantic completeness, enriched
> provenance, and end-to-end validation flow.

---

## 0 · Version History

| Version | Date | Type | Summary |
|----------|------|------|----------|
| ≤ v0.3.4 | 2025-09 | Core generator / logging | Deterministic stub + base CLI |
| **v0.3.5** | 2025-10-08 | Transport stabilization | First working Gemini→MCP flow using schema 0.7.3 |
| **v0.3.5a** | 2025-10-09 | Audit snapshot | Identified semantic/provenance/validation gaps |
| **v0.3.6** | 2025-10-09 | Semantic alignment (this spec) | Fills missing semantics, restores provenance, ensures strict validation passes unassisted |

---

## 1 · Scope

v0.3.6 resolves the semantic, provenance, and validation gaps identified in v0.3.5a.

Focus areas:
- Completing **Gemini schema binding and parsing** to match canonical contracts.  
- Populating **empty or underspecified sections** (shader, tone, haptic, control).  
- Restoring **enriched provenance** for schema ≥ 0.7.4 while preserving lean 0.7.3 output.  
- Reinstituting **`invoke_mcp`** in the CLI lifecycle for proper strict/relaxed validation.  
- Expanding tests so MCP strict validation passes without manual correction.

---

## 2 · Inherited Principles (from v0.3.5)

- Deterministic schema targeting (`LABS_SCHEMA_VERSION`) remains mandatory.  
- MCP remains the single source of truth for schema retrieval and validation.  
- JSONL logging and taxonomy format remain unchanged.  
- Gemini 2.0-flash stays the default live engine; OpenAI/deterministic are optional.

---

## 3 · Defaults

| Key | Value | Notes |
|-----|--------|-------|
| Schema version | 0.7.3 (baseline) | 0.7.4+ used only for enriched runs |
| Gemini model | `gemini-2.0-flash` | |
| Endpoint base | `https://generativelanguage.googleapis.com/v1beta/models/` | Full path = base + model + `:generateContent` |
| Config precedence | CLI → env → default | |
| Validation precedence | CLI flags → `LABS_FAIL_FAST` → default (`strict`) | Strict is now the baseline |

---

## 4 · Environment

| Var | Purpose |
|-----|----------|
| `LABS_SCHEMA_VERSION` | Target schema corpus (default `"0.7.3"`) |
| `LABS_FAIL_FAST` | Enables strict validation when `true` or `1` |
| `LABS_EXTERNAL_LIVE` | Enables live Gemini generation |
| `GEMINI_MODEL` | Gemini model identifier |
| `GEMINI_API_KEY` | API key for Gemini |
| `OPENAI_API_KEY` | Optional OpenAI key |
| `SYN_SCHEMAS_DIR` | Fallback local schema path |

All variables are loaded at preflight by `_load_env_file()` and merged into `os.environ`.

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
````

CLI usage:

```
labs generate "prompt" --engine gemini --schema-version 0.7.3 [--strict|--relaxed]
```

---

## 6 · Schema Retrieval (MCP)

All schemas must be fetched through MCP prior to normalization or validation.

```python
from mcp.core import get_schema
schema_resp = get_schema("synesthetic-asset")
schema = schema_resp["schema"]
```

* On failure → log `failure_mcp_unavailable`, abort in live mode.
* Deterministic mode may use local `meta/schemas/` stubs.

---

## 7 · Gemini Request / Response Contract

### 7.1 Request Structure

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

* Sanitized MCP schema embedded under `generation_config.response_schema`.
* `_sanitize_schema_for_gemini()` removes unsupported JSON Schema keys (`title`, `definitions`, `additionalProperties`, `$id`, etc.).
* Any missing `type` defaults to `"object"`.

### 7.2 Response Parsing

```python
def _parse_response(resp: dict) -> dict:
    text = resp["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text)
```

Alternate parsing paths (function-call args) are deprecated.

---

## 8 · Normalization & Semantic Filling

### 8.1 Fallback Filling (Schema 0.7.3)

Empty sections are populated with deterministic defaults to satisfy MCP strict validation.

| Section     | Fallback Source                   |
| ----------- | --------------------------------- |
| `shader`    | `AssetAssembler.default_shader()` |
| `tone`      | `AssetAssembler.default_tone()`   |
| `haptic`    | `AssetAssembler.default_haptic()` |
| `control`   | `_DEFAULT_CONTROL_PARAMETERS`     |
| `meta_info` | Static tags / schema examples     |

### 8.2 Provenance (≥ 0.7.4)

`_build_asset_provenance()` must emit:

```json
{
  "engine": "gemini",
  "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
  "trace_id": "<uuid4>",
  "input_parameters": { ... }
}
```

and attach to `meta_info.provenance` for enriched assets.

---

## 9 · CLI Lifecycle

1. **Preflight** — Load `.env`, resolve engine/schema/mode, generate `trace_id`.
2. **Schema Pull** — Fetch schema via MCP.
3. **Dispatch** — Call selected generator.
4. **Normalize** — Fill empty fields, inject provenance.
5. **Validate** — Use `invoke_mcp()` with proper strict/relaxed handling.
6. **Persist** — Write structured log entries with validation metadata.

---

## 10 · Validation Rules

* `$schema` must match resolved version.
* Structural fields may not be empty.
* `meta_info` must include at least one tag.
* Enriched schemas (≥ 0.7.4) must contain provenance keys.

---

## 11 · Error Classes

| Code               | Condition                       | Action       |
| ------------------ | ------------------------------- | ------------ |
| `auth_error`       | 401 / 403                       | stop         |
| `bad_request`      | 400 invalid body                | stop         |
| `network_error`    | timeout                         | retry ≤ 3    |
| `server_error`     | 5xx                             | retry ≤ 3    |
| `bad_response`     | malformed or empty output       | stop         |
| `validation_error` | strict validation failed        | stop / relax |
| `mcp_unavailable`  | MCP schema or validator offline | stop         |

---

## 12 · Logging

Every generation run emits structured JSONL entries to:

* `meta/output/labs/external.jsonl`
* `meta/output/labs/generator.jsonl`

Example record:

```json
{
  "timestamp": "2025-10-09T20:16:55Z",
  "engine": "gemini",
  "schema_version": "0.7.3",
  "trace_id": "c9c02ebb-a3f1-4108-a04b-ddc14cf2e759",
  "validation_status": "passed",
  "schema_binding": true,
  "taxonomy": "success"
}
```

---

## 13 · Tests / Exit Criteria

| Area                  | Requirement                                                          |
| --------------------- | -------------------------------------------------------------------- |
| Schema retrieval      | MCP returns valid dict                                               |
| Schema sanitization   | Only Gemini-supported fields survive                                 |
| Response parsing      | Uses canonical `candidates[0].content.parts[0].text` path            |
| Fallback filling      | Empty sections replaced with valid scaffolds                         |
| Provenance            | Enriched assets include engine, endpoint, trace_id, input_parameters |
| CLI validation        | `invoke_mcp()` executes correctly in both modes                      |
| MCP strict validation | Passes unassisted for schema 0.7.3                                   |
| CI                    | All tests green under `pytest -q`                                    |

---

## 14 · Non-Goals

* No schema version bump beyond 0.7.4.
* No cross-engine fallback expansion.
* No new operator or transport types.

---

## 15 · Reference Snippets

### Schema Fill Helpers

```python
def _fill_empty_sections(asset: dict) -> dict:
    for field, default_fn in {
        "shader": AssetAssembler.default_shader,
        "tone": AssetAssembler.default_tone,
        "haptic": AssetAssembler.default_haptic,
        "control": AssetAssembler.default_control,
    }.items():
        if not asset.get(field):
            asset[field] = default_fn()
    return asset
```

### CLI Validation Hook

```python
def _validate_asset(asset: dict, strict: bool = True):
    from labs.mcp.validate import invoke_mcp
    result = invoke_mcp(asset, strict=strict)
    if strict and not result.get("ok"):
        raise ValidationError("strict validation failed")
    return result
```

---

## 16 · Version Lineage Diagram

```
v0.3.4  →  v0.3.5  →  v0.3.5a  →  v0.3.6
(core)     (transport)   (audit)    (semantic)
 |----------- stabilized Gemini transport -----------|
 |---------------- semantic filling + validation ----------------|
```

---

### ✅ Summary

v0.3.6 closes the semantic loop opened in v0.3.5a.
Transport and schema binding remain stable; the focus shifts to **semantic fidelity and validation integrity**:

* Structural sections are auto-filled using schema-aware defaults.
* Enriched provenance reinstated for 0.7.4+.
* CLI → MCP validation path restored and verified.
* Strict MCP validation expected to pass unassisted.

This prepares Synesthetic Labs for **v0.3.7 (provenance-rich schema evolution)** and full parity across schema branches.