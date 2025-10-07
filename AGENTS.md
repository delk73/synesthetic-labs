# Synesthetic Labs Agents Audit (v0.3.5)

This update captures how the Generator and Critic agents line up with the v0.3.5 specification and where they still need work.

## Summary of Repo State
- Core agent coordination (schema branching, MCP validation handoff, external retry discipline) remains healthy.
- Environment bootstrapping still relies on a handwritten `.env` parser and lacks the `python-dotenv` adoption and GEMINI defaults mandated by the spec.
- Provenance/logging output trails the new expectations around taxonomy and input-parameter disclosure.

## Generator Agent
- Continues to branch between 0.7.3 legacy layouts and enriched ≥0.7.4 assets while injecting `$schema` and provenance data.
- Gemini integration issues structured requests (`contents → parts → text`, `responseMimeType='application/json'`) and retries 5xx responses, but its normalized assets omit the required `input_parameters` block inside the provenance object.
- External run logging persists to `meta/output/labs/external.jsonl` with engine/endpoint/trace IDs; taxonomy metadata is not yet recorded.

## Critic Agent
- Honors `LABS_FAIL_FAST`/CLI `--strict` & `--relaxed` flags when deciding whether MCP outages abort or downgrade reviews.
- Records MCP availability and validation outcomes in structured JSONL logs, preventing asset persistence when the validator reports `ok=False`.

## Transport & Environment
- MCP helpers still fall back to TCP sockets when an endpoint is missing, aligning with transport guarantees.
- The CLI warns about missing `LABS_EXTERNAL_LIVE`/API keys but ships no `.env.example`, leaving the toggle undocumented and the GEMINI model selection unset.

## Outstanding Work
1. Replace the bespoke `_load_env_file()` logic with `python-dotenv`, wire up GEMINI defaults, and add the dependency to `requirements.txt`.
2. Extend provenance normalization so generated assets surface `input_parameters` alongside existing trace data.
3. Add `taxonomy` fields to the external generation log schema and update tests to assert the richer payload.
4. Provide an `.env.example` (or equivalent docs) that highlights `LABS_EXTERNAL_LIVE` and other required keys under the new spec.
