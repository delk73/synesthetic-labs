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

---

## Historical Scopes

- **≤ v0.3.3**: Baseline generator/critic pipeline, transports, logging, patch lifecycle stubs, external scaffolding.
- **v0.3.4**: External API calls (Gemini/OpenAI), normalization contract, provenance, error taxonomy, logging, CI matrix.

---

## Scope (v0.3.5 Generator Schema Awareness)

### Objectives
- Add **schema version targeting** for asset generation.
- Generator output must include `$schema` pointing at correct corpus URL.
- Branch output:
  - **0.7.3**: emit legacy fields (root `name`, no enrichments).
  - **0.7.4+**: emit enriched fields (`asset_id`, `prompt`, `timestamp`, `parameter_index`, `provenance`, `effects`, `input_parameters`).
- Always run MCP validation against the declared `$schema`.

### Interfaces

#### Generator Contract
```python
def generate_asset(
    prompt: str,
    schema_version: str = "0.7.3",
    seed: Optional[int] = None,
    params: Optional[dict[str, Any]] = None,
    trace_id: Optional[str] = None
) -> dict:
    ...
