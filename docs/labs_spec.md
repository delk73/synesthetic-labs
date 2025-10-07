---
version: v0.3.5
lastReviewed: 2024-10-07
owner: labs-core
---

# Synesthetic Labs — Spec v0.3.5

## Scope
Defines generator behavior for Labs v0.3.5 using **Gemini 2.0-flash**.  
All assets target **schema 0.7.3** and must validate via MCP.

---

## 1 · Defaults
| Key | Value | Notes |
|-----|-------|-------|
| Schema version | 0.7.3 | |
| Gemini model | `gemini-2.0-flash` | |
| Endpoint base | `https://generativelanguage.googleapis.com/v1beta/models/` | The full URL is built from this + model name |
| Configuration precedence | CLI → env → default | Defines override order |
| Validation precedence | CLI (`--strict`/`--relaxed`) → env (`LABS_FAIL_FAST`) → default (`relaxed`) | |

---

## 2 · Environment
`labs` must preload `.env` and merge into `os.environ`.

| Var | Purpose |
|-----|----------|
| `LABS_SCHEMA_VERSION` | Target schema corpus (e.g., "0.7.3") |
| `LABS_FAIL_FAST` | If `true` or `1`, sets validation to strict. Overridden by CLI flags. |
| `LABS_EXTERNAL_LIVE` | Enable live API calls to external engines. |
| `GEMINI_MODEL` | Model name (e.g., `gemini-2.0-flash`). |
| `GEMINI_API_KEY` | Auth key for Google Gemini. |
| `OPENAI_API_KEY` | Optional auth key for the OpenAI engine. |

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
*   **gemini:** Calls the configured Gemini model endpoint. Requires `GEMINI_API_KEY`.
*   **openai:** Calls the configured OpenAI model endpoint. Requires `OPENAI_API_KEY`.
*   **deterministic:** Bypasses external calls. Returns a static, pre-defined JSON asset for testing purposes. Ignores the prompt.

---

## 4 · Request / Response

**Request body (Gemini)**

```json
{
  "contents": [
    {"role": "user", "parts": [{"text": "<prompt>"}]}
  ],
  "generationConfig": {"responseMimeType": "application/json"}
}
```

**Response parse**
The raw text from the LLM is parsed directly into a Python dictionary.
`candidates[0].content.parts[0].text` → `json.loads()`.

---

## 5 · Lifecycle

1.  **Preflight** – Load `.env`, resolve engine/schema/validation mode, and generate `trace_id`.
2.  **Dispatch** – Call the selected engine (`gemini`, `openai`, or `deterministic`).
3.  **Normalize** – Augment the raw dictionary from the engine.
    *   Add top-level `$schema` key.
    *   Generate and add the `provenance` object.
4.  **Validate** – Invoke MCP against the normalized asset.
  The MCP validator is now version-aware: it resolves the schema file based on the $schema URL embedded in the asset (e.g., .../0.7.3/... → meta/schemas/0.7.3/, .../0.7.4/... → meta/schemas/0.7.4/).
  If the specific version directory is missing use0.7.3
5.  **Persist** – Save the asset to disk only if validation passes (or generates a warning in relaxed mode).

---

## 6 · Provenance

Each asset includes a dynamically generated `provenance` object.

```json
"provenance": {
  "engine": "gemini-2.0-flash",
  "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
  "trace_id": "<uuid>",
  "timestamp": "<ISO8601>",
  "input_parameters": {
    "prompt": "<original_user_prompt>",
    "schema_version": "<requested_schema_version>",
    "seed": "<seed_if_provided>",
    "params": {
      "<any_extra_params>": "<value>"
    }
  }
}
```

---

## 7 · Error Classes

| Code | Condition | Action |
|---|---|---|
| `auth_error` | 401 / 403 | stop |
| `bad_request` | 400 (Invalid request from our side) | stop |
| `network_error` | Timeout / connection error | retry ≤ 3 |
| `server_error` | 5xx (Remote server issue) | retry ≤ 3 |
| `bad_response` | LLM response is not parsable JSON | stop |
| `validation_error` | Asset fails MCP validation | obey `LABS_FAIL_FAST` / CLI flags (abort on strict, warn on relaxed) |
| `mcp_unavailable` | Validator service is offline | obey `LABS_FAIL_FAST` / CLI flags |

---

## 8 · Logging

Append structured JSONL entries to the files below. Each line is a discrete JSON object.

*   `meta/output/labs/generator.jsonl`
*   `meta/output/labs/external.jsonl`

**Log entry fields:** `timestamp`, `engine`, `endpoint`, `schema_version`, `trace_id`, `result`, `taxonomy`.

### 8.1 · Taxonomy
The `taxonomy` field provides a classification of the generation outcome.

| Value | Meaning |
|---|---|
| `success` | Asset was generated and passed validation. |
| `success_with_warnings` | Asset was generated but only passed relaxed validation. |
| `failure_auth` | Authentication failed. |
| `failure_bad_request` | The request was malformed. |
| `failure_network` | Network-level error after retries. |
| `failure_server` | Remote server error after retries. |
| `failure_bad_response` | Could not parse the engine's response. |
| `failure_validation_strict` | Asset failed strict validation. |
| `failure_mcp_unavailable` | Validator was offline in strict mode. |

---

## 9 · Tests / Exit Criteria

| Area | Requirement |
|---|---|
| Schema branching | 0.7.3 / 0.7.4 verified |
| MCP schema resolution | Versioned `$schema` URLs correctly load matching schema folders 
| MCP | `strict` & `relaxed` modes pass and fail correctly |
| External | Gemini `gemini-2.0-flash` returns 200 OK |
| CLI | Env preload, flag precedence, and warnings are verified |
| CI | Baseline tests run against schema 0.7.3 using the `deterministic` engine |


---

## 10 · Non-Goals

*   No schema version bump in this release.
*   No complex fallback logic between engines.
*   No alternate transports (e.g., gRPC).