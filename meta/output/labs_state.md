# Synesthetic Labs State Report (v0.3.5a)

## Summary of Repo State

- Environment bootstrapping, external generator integrations, normalization, and structured logging all align with the v0.3.5a specification. Tests exercise schema binding, retry behaviour, and provenance outputs for both legacy and enriched schemas.
- MCP validation flows respect strict versus relaxed modes, although the CLI seeds `LABS_FAIL_FAST=false`, making relaxed mode the default unless callers opt into strict validation.
- The live schema pull test still depends on a developer-specific backend checkout, so it will fail outside an environment where that repository is available.

## Alignment

| Rule | Status | Evidence |
| --- | --- | --- |
| `env-preload-v0.3.5a` | Present | `labs/cli.py`: `_load_env_file()` loads `.env` and seeds `GEMINI_MODEL` / `GEMINI_API_KEY` / `LABS_FAIL_FAST` defaults.<br>`requirements.txt`: pins `python-dotenv`. |
| `external-live-toggle-v0.3.5a` | Present | `labs/generator/external.py`: `LABS_EXTERNAL_LIVE` drives mock versus live mode selection.<br>`.env.example`: documents `LABS_EXTERNAL_LIVE`. |
| `mcp-schema-pull-v0.3.5a` | Present | `labs/generator/external.py`: `_cached_schema_descriptor` pulls `get_schema("synesthetic-asset")` and reuses the returned spec.<br>`tests/test_mcp_schema_pull.py`: exercises `get_schema` / `list_schemas` via MCP. |
| `gemini-schema-binding-v0.3.5a` | Present | `labs/generator/external.py`: Gemini `generationConfig.responseSchema` references the live schema `$ref` and captures binding metadata.<br>`tests/test_external_generator.py`: asserts `schema_binding` appears in the external log. |
| `gemini-request-structure-v0.3.5a` | Present | `labs/generator/external.py`: Gemini payload builds `contents`→`parts`→`text` and sets `responseMimeType` to `application/json`. |
| `gemini-response-parse-v0.3.5a` | Present | `labs/generator/external.py`: parser reads `candidates[0].content.parts[0].text`, decodes JSON, and normalizes through the schema skeleton. |
| `normalization-schema-0.7.3-v0.3.5a` | Present | `labs/generator/assembler.py`: `_normalize_0_7_3` emits `$schema` and strips enriched fields such as provenance and parameter index.<br>`tests/test_external_generator.py`: legacy-schema test verifies `asset_id` / `timestamp` / `provenance` are absent. |
| `normalization-enriched-schema-v0.3.5a` | Present | `labs/generator/assembler.py`: enriched assets include `$schema`, `parameter_index`, and provenance scaffolding.<br>`labs/generator/external.py`: `_make_provenance_block` fills `engine`, `endpoint`, `trace_id`, and `input_parameters` for 0.7.4+.<br>`tests/test_external_generator.py`: enriched-schema test checks provenance metadata and taxonomy. |
| `error-handling-retry-v0.3.5a` | Present | `labs/generator/external.py`: retry loop iterates up to `max_retries` and classifies HTTP errors for retry decisions.<br>`tests/test_external_generator.py`: covers no-retry on auth errors and retries for rate limiting. |
| `structured-logging-v0.3.5a` | Present | `labs/logging.py`: `log_external_generation` writes JSONL with timestamps and schema binding defaults.<br>`labs/generator/external.py`: `record_run` logs engine, endpoint, taxonomy, and `schema_binding` into `external.jsonl`. |
| `mcp-validation-flow-v0.3.5a` | Present | `labs/cli.py`: generate/critique flows wire MCP validation, honour `--strict`/`--relaxed`, and persist assets only when MCP passes.<br>`labs/agents/critic.py`: `is_fail_fast_enabled()` toggles relaxed mode from `LABS_FAIL_FAST`.<br>`tests/test_pipeline.py`: CLI tests assert relaxed-mode warnings and `LABS_FAIL_FAST` overrides. |
| `mcp-version-aware-validator-v0.3.5a` | Present | `labs/mcp/validate.py`: `_resolve_schema_path` extracts schema versions and falls back to `meta/schemas/<version>`.<br>`tests/test_mcp_validator.py`: validates versioned and relative schema resolution plus caching. |

## Top Gaps & Fixes

1. **Schema pull test depends on a developer path.** `tests/test_mcp_schema_pull.py` references `/home/dce/src/sdfk-backend`, so the suite fails unless that checkout exists.
   * **Fix:** Stub MCP schema responses or vendor fixture data so the test runs in isolation.
2. **CLI defaults to relaxed validation.** `_load_env_file()` seeds `LABS_FAIL_FAST=false`, forcing callers to opt back into strict behaviour.
   * **Fix:** Default to strict (omit the env var or seed it to `true`) and rely on CLI flags/environment to request relaxed mode.

## Recommendations

- Replace the external MCP schema pull test with an isolated fixture-backed test so CI does not depend on a sibling repository.
- Revisit the default value for `LABS_FAIL_FAST` to keep strict validation as the baseline.
- Add an explicit test case covering HTTP 5xx retries to complement the rate-limit coverage.
