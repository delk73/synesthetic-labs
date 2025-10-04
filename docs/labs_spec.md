---
version: v0.3.5
lastReviewed: 2025-10-03
owner: labs-core
---

# Synesthetic Labs Spec

## Purpose

- Extend v0.3.4 by making the generator **schema-aware**.
- Allow Labs to produce assets that validate against a **declared schema corpus version** (`0.7.x`).
- Remove ad-hoc scrubbing: branching logic in generator ensures compatibility.
- Maintain reproducibility by embedding `$schema` in every generated asset.

---

## Historical Scopes

- **≤ v0.3.3**: Baseline generator/critic pipeline, transports, logging, patch lifecycle stubs, external scaffolding.
- **v0.3.4**: External API calls (Gemini/OpenAI), normalization contract, provenance, error taxonomy, logging, CI matrix.

---

## Scope (v0.3.5 Generator Schema Awareness)

### Objectives
- Add **schema version targeting** for asset generation.
- Generator output must include `$schema` pointing to the target corpus URL.
- Branch behavior:
  - **0.7.3**: emit legacy fields (root `name` required, no enrichment fields).
  - **0.7.4+**: emit enriched fields (`asset_id`, `prompt`, `timestamp`, `parameter_index`, `provenance`, `effects`, `input_parameters`); root `name` removed in favor of `meta_info.title`.
- Always run MCP validation against the declared `$schema`.

---

## Interfaces

#### Generator Contract
```python
def generate_asset(
    prompt: str,
    schema_version: str = "0.7.3",
    seed: Optional[int] = None,
    params: Optional[dict[str, Any]] = None,
    trace_id: Optional[str] = None
) -> dict:
    """
    Returns a normalized SynestheticAsset object
    that conforms to the target schema_version.
    """
```

#### CLI

```
labs generate --engine=<gemini|openai|deterministic> "prompt"
    [--seed <int>] [--temperature <float>] [--timeout-s <int>]
    [--schema-version <ver>]   # new
    [--strict|--relaxed]
```

* Precedence: `--schema-version` flag > `LABS_SCHEMA_VERSION` env > default (`0.7.3`).

---

## Environment Variables

| Var                                             | Purpose                             | Default / Notes |
| ----------------------------------------------- | ----------------------------------- | --------------- |
| `LABS_SCHEMA_VERSION`                           | Target schema version for generator | `"0.7.3"`       |
| *(all other vars from v0.3.4 remain unchanged)* |                                     |                 |

---

## Normalization Contract (updates)

* Every asset **must** include `$schema` root key:

  ```json
  {
    "$schema": "https://schemas.synesthetic.dev/0.7.3/synesthetic-asset.schema.json"
  }
  ```

* Branching rules:

  * **0.7.3**:

    * Require root `name`.
    * Forbid enrichment fields.
  * **0.7.4+**:

    * Drop root `name`; use `meta_info.title`.
    * Include enrichment fields (`asset_id`, `prompt`, `timestamp`, `parameter_index`, `provenance`, `effects`, `input_parameters`).

* Provenance injection rules remain unchanged from v0.3.4.

---

## Validation

* Same as v0.3.4:

  * Pre-flight checks (section presence, numeric bounds).
  * Always invoke MCP with strict JSON validation.
* Validation occurs **against the declared `$schema` version**.

---

## Logging

* Same files as v0.3.4 (`generator.jsonl`, `critic.jsonl`, `patches.jsonl`, `external.jsonl`).
* `external.jsonl` entries MUST include:

  * `schema_version`
  * `$schema` URL from the generated asset.

Example (truncated):

```json
{
  "ts": "2025-10-03T18:32:00Z",
  "trace_id": "1234-5678",
  "engine": "deterministic",
  "mode": "mock",
  "transport": "tcp",
  "schema_version": "0.7.3",
  "normalized_asset": { "$schema": "https://schemas.synesthetic.dev/0.7.3/synesthetic-asset.schema.json", ... },
  "mcp_result": { "ok": true, "errors": [] }
}
```

---

## Tests (matrix additions for v0.3.5)

* **Unit**

  * Generator emits valid `0.7.3` asset when configured.
  * Generator emits valid `0.7.4` asset when configured.
  * `$schema` tag matches chosen `schema_version`.
* **Integration**

  * `labs generate --schema-version=0.7.3` passes MCP validation with baseline schemas.
  * `labs generate --schema-version=0.7.4` passes MCP validation once schema corpus bumped.

---

## Exit Criteria (v0.3.5)

* Generator branching implemented and schema version configurable.
* All assets tagged with `$schema` and valid against chosen corpus.
* CI runs both `0.7.3` (baseline) and `0.7.4` (forward-looking).
* No ad-hoc stripping needed in Labs pipeline.

---

## Non-Goals

* No schema corpus bump bundled in this Labs spec.
* No new transports, no provider fine-tuning, no streaming APIs.
* No change to error taxonomy, retry, or security model (from v0.3.4).

---
