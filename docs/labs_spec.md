---
version: v0.3.4
lastReviewed: 2025-10-06
owner: labs-core
---

# Synesthetic Labs Spec (v0.3.4-core)

## Purpose
Define reproducible, schema-aware asset generation for the **Labs** toolchain.  
Ensure deterministic provenance, environment preload, and structured external-API output.

---

## 1 · Historical Scopes
| Version | Summary |
|----------|----------|
| ≤ v0.3.3 | Baseline generator / critic / transport / logging / patch stubs |
| **v0.3.4** | External API (Gemini / OpenAI), normalization, provenance, error taxonomy, CI matrix |
| ≥ v0.3.5 | Planned structured-output extension (already partially required here) |

---

## 2 · Schema-Targeting Hardening
- Generator **must branch** by `schema_version` and inject `$schema` → corpus URL.  
- 0.7.3 → legacy fields (`name` required; no enrichment).  
- 0.7.4 + → enriched fields (`asset_id`, `prompt`, `timestamp`, `parameter_index`, `provenance`, `effects`, `input_parameters`).  
- All generator outputs validated via **MCP** against declared `$schema`.

---

## 3 · Interfaces

### Generator Contract
```python
def generate_asset(
    prompt: str,
    schema_version: str = "0.7.3",
    seed: Optional[int] = None,
    params: Optional[dict[str, Any]] = None,
    trace_id: Optional[str] = None
) -> dict:
    """Return a normalized SynestheticAsset conforming to schema_version."""
```

### CLI Usage

```
labs generate --engine=<gemini|openai|deterministic> "prompt"
              [--schema-version <ver>] [--strict|--relaxed]
```

Precedence: flag → `LABS_SCHEMA_VERSION` → default `0.7.3`.

---

## 4 · Environment

| Var                   | Purpose                            | Default   |
| --------------------- | ---------------------------------- | --------- |
| `LABS_SCHEMA_VERSION` | Target schema corpus version       | `"0.7.3"` |
| `LABS_FAIL_FAST`      | Validation behaviour (1 = abort)   | `"1"`     |
| `GEMINI_API_KEY`      | Gemini API key (required for live) | –         |
| `OPENAI_API_KEY`      | OpenAI API key (required for live) | –         |

### Preload Rule

CLI **must preload** environment variables from a `.env` file —
either **manually** (for example, `_load_env_file`) **or via** a library such as `python-dotenv`.
The preload logic must:

1. Merge loaded values with `os.environ`.
2. Warn when critical keys (`GEMINI_API_KEY`, `OPENAI_API_KEY`) are missing.
3. Default to **mock mode** when no valid API keys are found.

---

## 5 · External Generation (Gemini / OpenAI)

### 5.1 Structured Output (Gemini)

1. Request body **must** follow Gemini `generateContent` schema:

   ```json
   {
     "contents": [
       {"role": "user", "parts": [{"text": "<prompt>"}]}
     ],
     "generationConfig": {"responseMimeType": "application/json"}
   }
   ```
2. Response must be parsed from
   `candidates[0].content.parts[0].text` → `json.loads()`.
3. Parsed JSON must form a valid Synesthetic Asset (`$schema` present).
4. Failure to produce valid JSON → `bad_response` taxonomy.

### 5.2 Headers & Limits

* Gemini: `X-Goog-Api-Key`.
* OpenAI: `Authorization: Bearer`.
* Enforce caps → 256 KiB request / 1 MiB response.
* Implement retry/back-off taxonomy; no-retry on 4xx.

---

## 6 · Normalization Contract

* Unknown top-level keys → `bad_response`.
* Wrong type → `bad_response`.
* Numeric bounds violations → `out_of_range`.
* Provenance block and `$schema` required in final asset.

---

## 7 · Validation Rules

* Always invoke MCP (strict & relaxed).
* **Strict:** abort on MCP failure (`mcp_unavailable`).
* **Relaxed:** log warning + return `ok:false`, no persistence.
* CLI must never persist assets when `ok:false`.

---

## 8 · Logging

* Write `generator.jsonl`, `critic.jsonl`, `patches.jsonl`, `external.jsonl`.
* Each entry includes: `engine`, `endpoint`, `schema_version`, `trace_id`, and `reason/detail` on failure.

---

## 9 · Testing Matrix (v0.3.4)

| Category    | Must Pass Checks                                            |
| ----------- | ----------------------------------------------------------- |
| Unit        | `$schema` stamped 0.7.3 / 0.7.4 branches                    |
| Integration | MCP validation strict/relaxed                               |
| External    | Gemini structured-output (`responseMimeType` + JSON decode) |
| CLI         | `.env` preload + warnings                                   |

---

## 10 · Exit Criteria

* Schema-branching operational and validated.
* `.env` preload present + warnings functional.
* MCP strict/relaxed modes verified.
* Gemini structured-output request/response validated end-to-end.
* CI baseline schemaVersion = 0.7.3.

---

## 11 · Non-Goals

No schema corpus bump; no new transports or retry policies; no taxonomy changes.

```

---