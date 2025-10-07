---
version: v0.3.5
lastReviewed: 2025-10-07
owner: labs-core
---

# Synesthetic Labs — Spec v0.3.5

## Scope
Defines generator behavior for Labs v0.3.5 using **Gemini 2.0-flash**.  
All assets target **schema 0.7.3** and must validate via MCP.

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
| `LABS_SCHEMA_VERSION` | Target schema corpus (e.g., `"0.7.3"`) |
| `LABS_FAIL_FAST` | If `true` or `1`, set validation = strict (override by CLI) |
| `LABS_EXTERNAL_LIVE` | Enable live external engine calls |
| `GEMINI_MODEL` | Gemini model name (e.g., `gemini-2.0-flash`) |
| `GEMINI_API_KEY` | Auth key for Gemini |
| `OPENAI_API_KEY` | Optional key for OpenAI engine |

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
    """Return SynestheticAsset conforming to schema_version."""
```

CLI:

```
labs generate --engine=<gemini|openai|deterministic> "prompt"
              [--schema-version <ver>] [--strict|--relaxed]
```

### 3.1 · Engine Behaviors

* **gemini** — calls Gemini 2.0-flash endpoint; requires `GEMINI_API_KEY`.
* **openai** — calls OpenAI endpoint; requires `OPENAI_API_KEY`.
* **deterministic** — bypasses external calls; returns static, schema-valid asset.

---

## 4 · Request / Response

**Request (Gemini)**

```json
{
  "contents": [
    {"role": "user", "parts": [{"text": "<prompt>"}]}
  ],
  "generationConfig": {"responseMimeType": "application/json"}
}
```

**Response parse**
`candidates[0].content.parts[0].text → json.loads()`

---

## 5 · Lifecycle

1. **Preflight** — Load `.env`, resolve engine/schema/mode, generate `trace_id`.
2. **Dispatch** — Call engine (`gemini` / `openai` / `deterministic`).
3. **Normalize** — Prepare asset for validation:

   * Add top-level `$schema` → `https://schemas.synesthetic.dev/0.7.3/synesthetic-asset.schema.json`.
   * For schema 0.7.3, **omit provenance and enrichment**.
   * For 0.7.4 and higher, include extended metadata (per future specs).
4. **Validate** — Run MCP on the normalized asset.

   * Resolver selects schema folder by URL (e.g., …/0.7.3/…).
   * Fallback to 0.7.3 if version dir missing.
5. **Persist** — Save to disk only if validation passes (or warns in relaxed mode).

---

## 6 · Meta Info (0.7.3 Baseline)

Schema 0.7.3 defines no `provenance`.
The optional `meta_info` object may include:

```json
{
  "category": "visual",
  "complexity": "medium",
  "tags": ["geometric", "reactive", "audio"]
}
```

All additional metadata or trace fields are reserved for ≥ 0.7.4.

---

## 7 · Error Classes

| Code               | Condition                  | Action                   |
| ------------------ | -------------------------- | ------------------------ |
| `auth_error`       | 401 / 403                  | stop                     |
| `bad_request`      | 400 invalid body           | stop                     |
| `network_error`    | timeout / connection error | retry ≤ 3                |
| `server_error`     | 5xx remote issue           | retry ≤ 3                |
| `bad_response`     | un-parsable LLM output     | stop                     |
| `validation_error` | MCP failure                | obey strict/relaxed mode |
| `mcp_unavailable`  | validator offline          | obey strict/relaxed mode |

---

## 8 · Logging

Append structured JSONL entries to:

* `meta/output/labs/generator.jsonl`
* `meta/output/labs/external.jsonl`

Each line is a JSON object with:
`timestamp`, `engine`, `endpoint`, `schema_version`, `trace_id`, `result`, `taxonomy`.

### 8.1 · Taxonomy

| Value                       | Meaning                         |
| --------------------------- | ------------------------------- |
| `success`                   | Generated and validated OK      |
| `success_with_warnings`     | Validated in relaxed mode       |
| `failure_auth`              | Authentication failed           |
| `failure_bad_request`       | Malformed request               |
| `failure_network`           | Network error after retries     |
| `failure_server`            | Server error after retries      |
| `failure_bad_response`      | Could not parse LLM output      |
| `failure_validation_strict` | Failed strict MCP validation    |
| `failure_mcp_unavailable`   | Validator offline (strict mode) |

---

## 9 · Tests / Exit Criteria

| Area                  | Requirement                                                       |
| --------------------- | ----------------------------------------------------------------- |
| Schema branching      | 0.7.3 and 0.7.4 paths branch cleanly                              |
| MCP schema resolution | Versioned `$schema` URLs load matching folders                    |
| MCP validation        | 0.7.3 assets pass without provenance fields                       |
| External              | Gemini `gemini-2.0-flash` returns 200 OK                          |
| CLI                   | Env preload, flag precedence, and warnings verified               |
| CI                    | Baseline tests run with schema 0.7.3 using `deterministic` engine |

---

## 10 · Non-Goals

* No schema version bump in this release.
* No cross-engine fallback logic.
* No alternate transports (e.g., gRPC).
* No enrichment or provenance for 0.7.3 assets.

```

---