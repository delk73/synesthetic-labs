---
version: v0.3.5
lastReviewed: 2025-10-08
owner: labs-core
---

# Synesthetic Labs — Spec v0.3.5

## Scope
Defines generator behavior for Labs v0.3.5 using **Gemini 2.0-flash**.  
All assets target **schema 0.7.3** and must validate through **MCP**.  
Schema retrieval is performed **programmatically via MCP core** (`get_schema`, `list_schemas`).

---

## 1 · Defaults
| Key | Value | Notes |
|-----|--------|-------|
| Schema version | 0.7.3 | baseline schema |
| Gemini model | `gemini-2.0-flash` | |
| Endpoint base | `https://generativelanguage.googleapis.com/v1beta/models/` | full URL = base + model + `:generateContent` |
| Configuration precedence | CLI → env → default | |
| Validation precedence | CLI (`--strict` / `--relaxed`) → env (`LABS_FAIL_FAST`) → default (`relaxed`) | |

---

## 2 · Environment
`labs` must preload `.env` and merge into `os.environ`.

| Var | Purpose |
|-----|----------|
| `LABS_SCHEMA_VERSION` | Target schema corpus (e.g. `"0.7.3"`) |
| `LABS_FAIL_FAST` | If `true` or `1`, enforce strict validation (overrides CLI) |
| `LABS_EXTERNAL_LIVE` | Enable live external engine calls |
| `GEMINI_MODEL` | Gemini model name (e.g. `gemini-2.0-flash`) |
| `GEMINI_API_KEY` | Auth key for Gemini |
| `OPENAI_API_KEY` | Optional key for OpenAI engine |
| `SYN_SCHEMAS_DIR` | Filesystem path to MCP schema corpus (fallback to backend `meta/schemas`) |

---

## 3 · Generator Contract
```python
def generate_asset(
    prompt: str,
    schema_version: str = "0.7.3",
    seed: int | None = None,
    params: dict[str, Any] | None = None,
    trace_id: str | None = None
) -> dict:
    """Return a SynestheticAsset conforming to schema_version."""
```

CLI:

```
labs generate --engine=<gemini|openai|deterministic> "prompt"
              [--schema-version <ver>] [--strict|--relaxed]
```

### 3.1 · Engine Behaviors

* **gemini** — calls Gemini 2.0-flash endpoint; requires `GEMINI_API_KEY`.
* **openai** — calls OpenAI endpoint; requires `OPENAI_API_KEY`.
* **deterministic** — bypasses external calls; returns static schema-valid asset.

---

## 4 · Schema Retrieval · (Required)

Labs must load schema definitions from MCP before normalization.

```python
from mcp.core import get_schema

schema_resp = get_schema("synesthetic-asset")
schema = schema_resp["schema"]
```

If the call fails:

* log `failure_mcp_unavailable`
* fallback to local stub under `schemas/` only in **deterministic** mode

The loaded schema drives all normalization defaults, validation, and `$schema` URL resolution.

---

## 5 · Request / Response

**Request (Gemini):**

```json
{
  "contents": [
    {"role": "user", "parts": [{"text": "<prompt>"}]}
  ],
  "generation_config": {"response_mime_type": "application/json"}
}
```

**Response parse:**
`candidates[0].content.parts[0].text → json.loads()`

---

## 5.1 · Schema-Bound Generation (New)

When using the **Gemini** engine, Labs must **bind the live MCP schema** to the Gemini request to ensure the model produces JSON conforming to the canonical Synesthetic schema.

### Behavior

1. **Schema Retrieval**

   ```python
   schema_resp = get_schema("synesthetic-asset")
   schema = schema_resp["schema"]
   schema_url = schema.get("$id")
   ```

   If schema retrieval fails, log `failure_mcp_unavailable` and abort in live mode.
   Only deterministic mode may use local schema stubs.

2. **Request Construction**

   The Gemini 2.0 API requires structured output schemas to be declared via
   `tools.function_declarations[].parameters`. Labs sanitizes the MCP schema before
   embedding it: the sanitizer keeps only the Gemini-supported fields (`type`,
   `format`, `description`, `properties`, `items`, `required`, `enum`) and recursively
   drops everything else (`$schema`, `$id`, `title`, `definitions`,
   `additionalProperties`, etc.). Any object without an explicit type defaults to
   `"object"` so Gemini receives a valid contract.

   ```json
   {
     "contents": [
       {"role": "user", "parts": [{"text": "<prompt>"}]}
     ],
     "generation_config": {
       "response_mime_type": "application/json"
     },
     "tools": [
       {
         "function_declarations": [
           {
             "name": "output",
             "description": "Synesthetic asset JSON response",
             "parameters": {
               "type": "object",
               "properties": {
                 "name": {"type": "string"},
                 "shader": {"type": "object"},
                 "tone": {"type": "object"},
                 "haptic": {"type": "object"},
                 "control": {"type": "object"},
                 "meta_info": {"type": "object"},
                 "modulations": {
                   "type": "array",
                   "items": {"type": "object"}
                 },
                 "rule_bundle": {"type": "object"},
                 "provenance": {"type": "object"}
               },
               "required": ["name", "shader", "tone", "haptic", "control", "meta_info"]
             }
           }
         ]
       }
    ],
    "tool_config": {
      "function_calling_config": {
        "mode": "AUTO"
      }
    },
     "model": "gemini-2.0-flash"
   }
   ```

   The schema content is sourced from the MCP service (e.g.
   `https://schemas.synesthetic.dev/0.7.3/synesthetic-asset.schema.json`) and then
   sanitized using this whitelist before being sent to Gemini.

3. **Response Parsing**

   Gemini output must already match this schema.
   `_normalize_asset()` is limited to:

   * stamping `$schema` with the resolved URL
   * injecting or adjusting `meta_info`
   * leaving structural fields (`shader`, `tone`, `haptic`, `control`, `rule_bundle`) untouched.

4. **Validation**

   Because generator and MCP validator share the same schema object, strict validation should pass with zero diffs.

5. **Telemetry**

   Every Gemini request must log `"schema_binding": true` in
   `meta/output/labs/external.jsonl`.

6. **Failure Modes**

   | Condition                        | Code                        | Action                 |
   | -------------------------------- | --------------------------- | ---------------------- |
   | Schema pull failed               | `failure_mcp_unavailable`   | stop                   |
   | Gemini rejected schema binding   | `failure_bad_request`       | stop                   |
   | Output invalid under strict mode | `failure_validation_strict` | stop or relax per mode |

### Example Implementation

```python
def _build_gemini_request(prompt: str, schema_version="0.7.3"):
    schema_resp = get_schema("synesthetic-asset")
    if not schema_resp.get("ok"):
        raise RuntimeError("MCP schema unavailable")
    schema = sanitize_for_gemini(schema_resp["schema"])
    return {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generation_config": {"response_mime_type": "application/json"},
        "tools": [{
            "function_declarations": [{
                "name": "output",
                "description": "Synesthetic asset JSON response",
                "parameters": schema,
            }]
        }],
        "tool_config": {"function_calling_config": {"mode": "AUTO"}},
        "model": "gemini-2.0-flash",
    }
```

---

## 6 · Lifecycle

1. **Preflight** — Load `.env`, resolve engine/schema/mode, generate `trace_id`.
2. **Schema Pull** — Call `mcp.core.get_schema(LABS_SCHEMA_VERSION)` to load canonical schema dict.
3. **Dispatch** — Call engine (`gemini` / `openai` / `deterministic`).
4. **Normalize** — Construct asset scaffold directly from the pulled schema:

   * Apply `default` or first `examples` values for missing fields.
   * Add `$schema` → URL from schema `$id`.
   * Omit `provenance` / `enrichment` for 0.7.3.
5. **Validate** — Send to MCP validator (same schema object).

   * On strict mode → fail if invalid.
   * On relaxed mode → warn and persist with flag.
6. **Persist** — Write only if validation passed or relaxed.

---

## 7 · Meta Info (0.7.3 Baseline)

Schema 0.7.3 defines no `provenance`.
Optional `meta_info` object may include:

```json
{
  "category": "visual",
  "complexity": "medium",
  "tags": ["geometric", "reactive", "audio"]
}
```

---

## 8 · Error Classes

| Code               | Condition                            | Action              |
| ------------------ | ------------------------------------ | ------------------- |
| `auth_error`       | 401 / 403                            | stop                |
| `bad_request`      | 400 invalid body                     | stop                |
| `network_error`    | timeout / connection error           | retry ≤ 3           |
| `server_error`     | 5xx remote issue                     | retry ≤ 3           |
| `bad_response`     | un-parsable LLM output               | stop                |
| `validation_error` | MCP validation failure               | obey strict/relaxed |
| `mcp_unavailable`  | MCP schema pull or validator offline | obey strict/relaxed |

---

## 9 · Logging

Write structured JSONL entries to:

* `meta/output/labs/generator.jsonl`
* `meta/output/labs/external.jsonl`

Each entry includes:
`timestamp`, `engine`, `endpoint`, `schema_version`, `trace_id`, `result`, `taxonomy`.

### 9.1 · Taxonomy

| Value                       | Meaning                          |
| --------------------------- | -------------------------------- |
| `success`                   | Generated and validated OK       |
| `success_with_warnings`     | Validated in relaxed mode        |
| `failure_auth`              | Authentication failed            |
| `failure_bad_request`       | Malformed request                |
| `failure_network`           | Network error after retries      |
| `failure_server`            | Server error after retries       |
| `failure_bad_response`      | Could not parse LLM output       |
| `failure_validation_strict` | Failed strict MCP validation     |
| `failure_mcp_unavailable`   | Schema pull or validator offline |

---

## 10 · Tests / Exit Criteria

| Area                  | Requirement                                                       |
| --------------------- | ----------------------------------------------------------------- |
| Schema retrieval      | `mcp.core.get_schema()` succeeds and returns valid dict           |
| Schema branching      | 0.7.3 and 0.7.4 paths branch cleanly                              |
| MCP schema resolution | Versioned `$schema` URLs map to matching folders                  |
| MCP validation        | 0.7.3 assets pass without provenance                              |
| External              | Gemini `gemini-2.0-flash` returns 200 OK                          |
| CLI                   | Env preload, flag precedence, warnings verified                   |
| CI                    | Baseline tests run with schema 0.7.3 using `deterministic` engine |

---

## 11 · Non-Goals

* No schema version bump in this release.
* No cross-engine fallback logic.
* No alternate transports (e.g. gRPC).
* No enrichment or provenance for 0.7.3 assets.

---

## 12 · Reference Implementation Snippet

```python
from mcp.core import get_schema

def _normalize_asset(asset, schema_version="0.7.3"):
    schema_resp = get_schema("synesthetic-asset")
    if not schema_resp["ok"]:
        raise RuntimeError("Schema pull failed")
    schema = schema_resp["schema"]
    normalized = {}
    for key, spec in schema["properties"].items():
        if "default" in spec:
            normalized[key] = spec["default"]
        elif "examples" in spec and spec["examples"]:
            normalized[key] = spec["examples"][0]
        else:
            normalized[key] = None
    normalized.update({
        "$schema": schema.get("$id"),
        "name": asset.get("name"),
        "description": asset.get("description"),
        "meta_info": {"category": "autogenerated"}
    })
    return normalized
```

---

### ✅ Summary

v0.3.5 formalizes MCP schema pull **and** schema-bound Gemini generation.
All Gemini requests must embed the sanitized MCP schema in `tools.function_declarations[0].parameters` and log the `$id` within the `schema_binding` metadata.
Normalization is reduced to metadata stamping; structural compliance is guaranteed at generation.
Strict MCP validation is expected to pass without manual correction.
