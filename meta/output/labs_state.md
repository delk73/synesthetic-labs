# Synesthetic Labs State Report (v0.3.5a)

## Summary of Repo State

An audit of the current repository against the v0.3.5a specification uncovered several compliance gaps:

- **Environment & Configuration**: Environment preloading and the `LABS_EXTERNAL_LIVE` toggle operate as expected, ensuring local defaults and live-mode gating behave per spec.
- **Schema & Generation**: MCP schemas are fetched and used to seed request scaffolding, but Gemini integration diverges from the required `generation_config.response_schema` binding and canonical response parsing contract.
- **Normalization**: Legacy (`0.7.3`) normalization trims enriched fields correctly, while enriched (`0.7.4+`) assets omit the spec-mandated provenance details (engine, endpoint, trace_id, input parameters).
- **Lifecycle & Validation**: External retry logic, structured logging, and validator schema resolution align with expectations; however, the CLI flow does not surface the required `invoke_mcp` call path for strict/relaxed validation management.

## Alignment

| Rule | Status | Evidence |
| --- | --- | --- |
| `env-preload-v0.3.5a` | Present | `labs/cli.py`: `_load_env_file()` loads `.env`, seeds `GEMINI_MODEL`, `LABS_FAIL_FAST`, and checks `GEMINI_API_KEY`.<br>`requirements.txt`: includes `python-dotenv`. |
| `external-live-toggle-v0.3.5a` | Present | `labs/cli.py`: warns when `LABS_EXTERNAL_LIVE` unset and respects it for mock mode.<br>`.env.example`: documents `LABS_EXTERNAL_LIVE`. |
| `mcp-schema-pull-v0.3.5a` | Present | `labs/generator/external.py`: `_cached_schema_descriptor()` calls `get_schema('synesthetic-asset')` and returns defaults.<br>`tests/test_mcp_schema_pull.py`: exercises `get_schema`/`list_schemas`. |
| `gemini-schema-binding-v0.3.5a` | Divergent | `labs/generator/external.py`: `_build_request()` injects sanitized schema under `tools.function_declarations` instead of `generation_config.response_schema`.<br>No references to `response_schema` in the module, so Gemini requests lack the mandated field. |
| `gemini-request-structure-v0.3.5a` | Present | `labs/generator/external.py`: Gemini payload includes `contents/parts/text` and `generation_config.response_mime_type='application/json'`. |
| `gemini-response-parse-v0.3.5a` | Divergent | `labs/generator/external.py`: `_parse_response()` prefers function-call args and only falls back to arbitrary part text, deviating from the required `candidates[0].content.parts[0].text` contract. |
| `normalization-schema-0.7.3-v0.3.5a` | Present | `labs/generator/assembler.py`: `_normalize_0_7_3()` returns a lean payload with `$schema`, trimmed sections, and no enriched fields. |
| `normalization-enriched-schema-v0.3.5a` | Divergent | `labs/generator/assembler.py`: `_build_asset_provenance()` omits `endpoint` and `input_parameters`, so enriched assets lack the required provenance details.<br>`tests/test_generator.py`: does not assert on endpoint/input parameters, leaving the gap untested. |
| `error-handling-retry-v0.3.5a` | Present | `labs/generator/external.py`: retry loop replays requests up to `max_retries`, and `_classify_http_error()` retries only on 5xx/rate-limit codes. |
| `structured-logging-v0.3.5a` | Present | `labs/logging.py`: `log_external_generation()` writes JSONL with `schema_binding` default.<br>`labs/generator/external.py`: `record_run()` emits engine/endpoint/trace_id/taxonomy/schema_binding fields. |
| `mcp-validation-flow-v0.3.5a` | Missing | `labs/cli.py`: generation flow routes through `CriticAgent` but never calls the required `invoke_mcp`, so strict/relaxed handling bypasses the mandated entry point. |
| `mcp-version-aware-validator-v0.3.5a` | Present | `labs/mcp/validate.py`: `_resolve_schema_path()` extracts semantic version, checks `meta/schemas/<version>/...`, and falls back appropriately. |

## Top Gaps & Fixes

1. **Gemini schema binding**: Relocate the sanitized MCP schema into `generation_config.response_schema` and log `schema_binding: true` from that pathway to satisfy the binding contract.
2. **Gemini response parsing**: Normalize responses by decoding `candidates[0].content.parts[0].text` (after enforcing presence) and drop the alternate function-call branch.
3. **Enriched provenance**: Extend `_build_asset_provenance()` (and related normalization paths) to populate engine, endpoint, trace ID, and input parameter records per spec, and cover with regression tests.
4. **CLI validation flow**: Reintroduce the explicit `invoke_mcp` helper so `--strict/--relaxed` flags and `LABS_FAIL_FAST` drive the mandated lifecycle.

## Recommendations

- Add regression tests that assert on the precise Gemini request/response structure, including `generation_config.response_schema` and the `candidates[0].content.parts[0].text` parsing path.
- Enhance assembler tests to verify enriched provenance payloads carry engine, endpoint, trace ID, and input parameter metadata.
- Implement CLI integration tests that exercise both strict and relaxed validation modes, ensuring `invoke_mcp` is invoked with the correct semantics before persistence.
- Document the updated Gemini schema-binding behavior in `docs/specs/synesthetic_labs_v0.3.5.md` once remediated to keep operators aligned with the contract.
