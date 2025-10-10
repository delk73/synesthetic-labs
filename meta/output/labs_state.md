# Synesthetic Labs State Report (v0.3.6)

## Summary of Repo State

- **Environment & Configuration**: The CLI still preloads `.env`, seeds required defaults, and warns when Gemini and live-mode variables are absent, keeping environment handling aligned with spec expectations.
- **Schema & Generation**: MCP schemas load correctly, yet Gemini requests continue to rely on function declarations instead of `generation_config.response_schema`, and response parsing still prioritizes deprecated function-call payloads.
- **Normalization & Provenance**: Legacy (0.7.3) assets are assembled with the expected scaffolding, but enriched payloads omit engine/endpoint/input-parameter provenance despite deterministic section filling.
- **Lifecycle & Validation**: Structured logging and retry handling remain compliant, but the CLI never calls `invoke_mcp` and relaxed validation mode refuses to persist assets, leaving the v0.3.6 lifecycle requirements unmet.

## Alignment

| Rule | Status | Evidence |
| --- | --- | --- |
| `env-preload-v0.3.6` | Present | `labs/cli.py`: `_load_env_file()` loads `.env`, seeds `GEMINI_MODEL`, `LABS_FAIL_FAST`, and `LABS_SCHEMA_VERSION`, and warns when `GEMINI_API_KEY`/`LABS_EXTERNAL_LIVE` are missing (lines 15-40).<br>`requirements.txt`: pins `python-dotenv` for runtime support (line 4). |
| `mcp-schema-pull-v0.3.6` | Present | `labs/generator/external.py`: `_cached_schema_descriptor()` calls `get_schema('synesthetic-asset', version=...)` and returns schema metadata (lines 94-105).<br>`tests/test_mcp_schema_pull.py`: integration test exercises `get_schema`/`list_schemas` success paths (lines 4-30). |
| `gemini-schema-binding-v0.3.6` | Divergent | `labs/generator/external.py`: `_build_request()` injects sanitized schema under `tools.function_declarations` and never populates `generation_config.response_schema` (lines 1654-1705). |
| `gemini-response-parse-v0.3.6` | Divergent | `labs/generator/external.py`: `_parse_response()` still favors `function_call` args and only falls back to arbitrary part text instead of enforcing `candidates[0].content.parts[0].text` (lines 1815-1861). |
| `normalization-schema-0.7.3-v0.3.6` | Present | `labs/generator/assembler.py`: `_build_legacy_asset()` emits `$schema`, timestamps, and ensures shader/tone/haptic/control scaffolds plus trimmed rule/modulation sections (lines 151-200). |
| `provenance-enriched-schema-v0.3.6` | Divergent | `labs/generator/assembler.py`: `_build_asset_provenance()` lacks engine, endpoint, trace_id propagation, and omits `input_parameters`, so enriched assets stay under-populated (lines 584-603). |
| `cli-validation-flow-v0.3.6` | Missing | `labs/cli.py`: generation flow delegates to `CriticAgent.review()` without ever importing or invoking `invoke_mcp`, leaving strict/relaxed routing outside the mandated helper (lines 201-254).<br>`labs/mcp/validate.py`: module only exports `validate_asset`/`validate_many`, with no `invoke_mcp` entry point (lines 1-141). |
| `error-handling-retry-v0.3.6` | Present | `labs/generator/external.py`: `generate()` limits attempts to `max_retries` and records retry metadata (lines 380-470).<br>`labs/generator/external.py`: `_classify_http_error()` retries only on 5xx/429 while 4xx return non-retryable failures (lines 773-825). |
| `structured-logging-v0.3.6` | Present | `labs/logging.py`: `log_external_generation()` writes JSONL records with timestamp and `schema_binding` field (lines 30-35).<br>`labs/generator/external.py`: `record_run()` logs engine, endpoint, trace_id, validation_status, and schema_binding into `external.jsonl` (lines 572-628). |
| `validation-passes-v0.3.6` | Divergent | `labs/cli.py`: assets persist only when `_review_mcp_ok(review)` succeeds; relaxed mode falls through without persistence despite warnings (lines 204-224). |
| `fallback-filling-v0.3.6` | Present | `labs/generator/external.py`: `_normalise_asset()` and `_build_control_section()` backfill shader/tone/haptic/control defaults with deterministic scaffolds and control parameters (lines 837-940, 1213-1241). |

## Top Gaps & Fixes

1. **Gemini schema binding**: Populate `generation_config.response_schema` with the sanitized MCP schema and surface a `schema_binding: true` log entry sourced from that binding.
2. **Gemini response parsing**: Replace the function-call parsing branch with strict decoding of `candidates[0].content.parts[0].text`, raising structured errors when the contract is violated.
3. **Validation lifecycle**: Introduce the `invoke_mcp(..., strict=...)` helper in CLI flows so strict/relaxed modes behave per v0.3.6, and allow relaxed mode to persist assets with explicit warnings.
4. **Enriched provenance**: Extend `_build_asset_provenance()` to include engine, endpoint, trace identifiers, and input parameters for schema ≥0.7.4, mirroring spec defaults.

## Recommendations

- Add Gemini request/response regression tests that assert `generation_config.response_schema` binding and the canonical text-parsing path.
- Expand assembler coverage to validate enriched provenance blocks carry engine, endpoint, trace_id, and input parameter metadata.
- Update CLI integration tests to confirm relaxed mode persists assets after invoking `invoke_mcp` with `strict=False` semantics.
- Document the revised schema binding and validation flow in `docs/specs/synesthetic_labs_v0.3.6.md` once remediated.
