---
version: v0.3.4
lastReviewed: 2025-10-06
owner: labs-core
---

# Synesthetic Labs Spec

## Purpose

- Make the generator **schema-aware** and reproducible.
- Produce assets that validate against a declared **schema corpus version** (`0.7.x`).
- Remove ad-hoc scrubbing; branching logic ensures compatibility.
- Embed `$schema` in every generated asset for deterministic provenance.

---

## Historical Scopes

- **≤ v0.3.3** — Baseline generator/critic pipeline, transports, logging, patch lifecycle stubs.
- **v0.3.4** — External API calls (Gemini / OpenAI), normalization contract, provenance, error taxonomy, logging, CI matrix.

> Future versions (≥ v0.3.5) build on this baseline.

---

## Scope (Schema Targeting Hardening)

### Objectives
- Add **schema-version targeting** for generation.
- Generator output must include `$schema` → target corpus URL.
- Branch behavior:
  - **0.7.3** → legacy fields (`name` required; no enrichment).
  - **0.7.4 +** → enriched fields (`asset_id`, `prompt`, `timestamp`, `parameter_index`, `provenance`, `effects`, `input_parameters`).
- Always run MCP validation against the declared `$schema`.

---

## Interfaces

### Generator Contract
```python
def generate_asset(
    prompt: str,
    schema_version: str = "0.7.3",
    seed: Optional[int] = None,
    params: Optional[dict[str, Any]] = None,
    trace_id: Optional[str] = None
) -> dict:
    """Return a normalized SynestheticAsset object conforming to schema_version."""
```

### CLI

```
labs generate --engine=<gemini|openai|deterministic> "prompt"
    [--seed <int>] [--temperature <float>] [--timeout-s <int>]
    [--schema-version <ver>]
    [--strict|--relaxed]
```

*Precedence:* `--schema-version` > `LABS_SCHEMA_VERSION` > default (`0.7.3`).

---

## Environment Variables

| Var                   | Purpose                                       | Default / Notes          |
| --------------------- | --------------------------------------------- | ------------------------ |
| `LABS_SCHEMA_VERSION` | Target schema corpus version                  | `"0.7.3"`                |
| `LABS_FAIL_FAST`      | Validation behavior (1 = abort, 0 = degraded) | `"1"`                    |
| `GEMINI_API_KEY`      | Gemini API key                                | Required for live Gemini |
| `OPENAI_API_KEY`      | OpenAI API key                                | Required for live OpenAI |

### Environment Preload

The CLI **must load** a `.env` file at startup via `python-dotenv`.
If critical keys (`GEMINI_API_KEY`, `OPENAI_API_KEY`) are missing, the CLI logs a warning and falls back to mock mode.

---

## External Generation (v0.3.5 extension)

### Structured Output for Gemini

* Gemini integrations **must** set
  `"generationConfig":{"responseMimeType":"application/json"}`
  to enforce JSON-structured responses.
* Returned content is parsed from
  `candidates[0].content.parts[0].text`
  and must decode to a valid Synesthetic asset JSON object.
* This replaces prior ad-hoc text-to-JSON parsing.

---

## Normalization Contract

* Every asset includes a `$schema` root key.
* Branching rules identical to prior spec.
* Provenance injection unchanged.

---

## Validation Rules

* Always invoke MCP with strict JSON validation.
* Validate against the declared `$schema`.
* If MCP unreachable:

  * **Strict (`LABS_FAIL_FAST=1`)** → abort with `mcp_unavailable`.
  * **Relaxed (`LABS_FAIL_FAST=0`)** → return review with
    `ok:false`, `reason:"mcp_unavailable"`, `validation_status:"degraded"`.
* CLI never persists assets when `ok:false`.
* Each review must include a full `mcp_response` block.

---

## Logging

* Output files: `generator.jsonl`, `critic.jsonl`, `patches.jsonl`, `external.jsonl`.
* Each `external.jsonl` entry records `schema_version` and `$schema` URL.

Example:

```json
{
  "ts": "2025-10-06T18:32:00Z",
  "engine": "gemini",
  "schema_version": "0.7.3",
  "normalized_asset": {"$schema": "https://schemas.synesthetic.dev/0.7.3/synesthetic-asset.schema.json"},
  "mcp_result": {"ok": true, "errors": []}
}
```

---

## Tests (Matrix Additions for v0.3.5)

**Unit**

* Generator emits valid 0.7.3 and 0.7.4 assets.
* `$schema` matches chosen version.

**Integration**

* `labs generate --schema-version=0.7.3` passes MCP validation.
* CLI warns if `.env` incomplete.
* Critic strict mode aborts on MCP outage; relaxed logs & blocks persistence.
* Gemini structured-output path verified via `responseMimeType`.

---

## Exit Criteria

* Schema-version branching operational.
* `.env` auto-load and validation implemented.
* `$schema` tagging enforced.
* MCP enforcement in both modes; no persistence on failure.
* Gemini structured-output contract validated.
* CI baseline: `schemaVersion=0.7.3`.

---

## Non-Goals

* No schema corpus bump.
* No new transports, streaming APIs, or retry policy changes.
* No alteration to error taxonomy or security model.

---
