# Synesthetic Labs State Report (v0.3.6)

## Summary of Repo State

- **Environment & configuration**: CLI still preloads `.env`, sets defaults for `LABS_SCHEMA_VERSION`, `GEMINI_MODEL`, `LABS_FAIL_FAST`, and surfaces warnings for missing live-mode credentials; `LABS_EXTERNAL_LIVE` continues to gate live transport selection.
- **Schema binding & parsing**: MCP schemas load correctly, but Gemini requests still send a `$ref` pointer instead of the sanitized schema body and response parsing keeps deprecated `function_call` branches.
- **Normalization & provenance**: Legacy (`0.7.3`) normalization retains provenance data, and enriched assets omit endpoint/input parameter provenance when assembled internally.
- **Lifecycle & validation**: Retries, logging, and section backfills meet spec, yet the CLI never calls `invoke_mcp`, relaxed generation skips persistence, and strict validation relies on indirect Critic flows.

## Alignment

| Rule | Status | Evidence |
| --- | --- | --- |
| `env-preload-v0.3.6` | Present | `labs/cli.py`: `_load_env_file()` calls `load_dotenv`, seeds `LABS_SCHEMA_VERSION`/`GEMINI_MODEL`/`LABS_FAIL_FAST`, and logs when `GEMINI_API_KEY`/`LABS_EXTERNAL_LIVE` are missing.<br>`labs/cli.py`: `main()` reads `LABS_SCHEMA_VERSION` for defaults and warns globally when live creds are absent. |
| `mcp-schema-pull-v0.3.6` | Present | `labs/generator/external.py`: imports `get_schema` and `_schema_descriptor()` delegates to `get_schema("synesthetic-asset", version=...)` before building requests.<br>`tests/test_mcp_schema_pull.py`: exercises `get_schema`/`list_schemas` happy paths. |
| `gemini-schema-binding-v0.3.6` | Divergent | `labs/generator/external.py`: `_build_request()` sets `generation_config["response_schema"] = {"$ref": schema_id}` without sanitizing the MCP document.<br>`tests/test_external_generator.py`: still asserts function declaration parameters instead of `response_schema`. |
| `gemini-response-parse-v0.3.6` | Divergent | `labs/generator/external.py`: `_parse_response()` prefers `function_call` args, only falling back to text parts, keeping deprecated parsing paths.<br>`tests/test_external_generator.py`: mocks continue validating the legacy function-call behavior. |
| `normalization-schema-0.7.3-v0.3.6` | Divergent | `labs/generator/assembler.py`: `_normalize_0_7_3()` copies `meta_info["provenance"]` into the legacy asset despite the 0.7.3 omission requirement.<br>`labs/generator/external.py`: legacy normalization just forwards meta provenance instead of stripping it. |
| `provenance-enriched-schema-v0.3.6` | Divergent | `labs/generator/assembler.py`: `_build_asset_provenance()` emits `generator` metadata without `endpoint` or `input_parameters` fields.<br>`tests/test_generator.py`: enriched schema assertions stop at presence of `provenance`, not the required fields. |
| `cli-validation-flow-v0.3.6` | Missing | `labs/cli.py`: generation path sends assets to `CriticAgent.review()` but never calls `invoke_mcp(..., strict=...)` nor honors CLI flags through that helper.<br>`labs/mcp/validate.py`: exports only `validate_asset`/`validate_many` with no `invoke_mcp` entry point. |
| `error-handling-retry-v0.3.6` | Present | `labs/generator/external.py`: `_classify_http_response()` retries on `>=500`/`429` and marks 4xx as non-retryable.<br>`tests/test_external_generator.py`: `test_rate_limited_retries` and `test_no_retry_on_auth_error` cover 503 retries vs. 400 failures. |
| `structured-logging-v0.3.6` | Present | `labs/generator/external.py`: `record_run()` writes `external.jsonl` entries with engine, endpoint, trace_id, validation_status, and schema binding metadata.<br>`labs/logging.py`: `log_external_generation()` persists structured JSON to `meta/output/labs/external.jsonl`. |
| `validation-passes-v0.3.6` | Divergent | `labs/cli.py`: assets persist only when `_review_mcp_ok(review)` is truthy; relaxed failures skip `_persist_asset()`, contradicting relaxed-mode persistence.<br>`tests/test_pipeline.py`: relaxed-mode generation asserts no files are written under `experiments/`. |
| `fallback-filling-v0.3.6` | Present | `labs/generator/external.py`: `_merge_structured_section()` overlays payloads onto `_DEFAULT_SECTIONS` for shader/tone/haptic/control scaffolds.<br>`labs/generator/external.py`: `_build_control_section()` and `_build_control_parameters()` backfill deterministic control mappings when inputs are empty. |

## Top gaps & fixes

1. **Schema-bound Gemini contract**: Replace the `$ref` placeholder with `_sanitize_schema_for_gemini()` and bind through `generation_config.response_schema`, updating fixtures to match.
2. **Response parsing**: Drop `function_call` decoding and enforce `candidates[0].content.parts[0].text` JSON parsing with clear error handling.
3. **Normalization parity**: Strip provenance when targeting `0.7.3`, enrich `_build_asset_provenance()` with endpoint/input parameters, and extend tests to assert those fields.
4. **MCP lifecycle**: Implement `invoke_mcp()` in `labs/mcp/validate.py` and route `labs/cli.py` through it so strict/relaxed flows obey spec while persisting relaxed assets with warnings.

## Recommendations

- Add Gemini request/response regression tests that assert `generation_config.response_schema` contains the sanitized schema and that responses are decoded exclusively from the first text part.
- Expand assembler and CLI test coverage to ensure legacy normalization omits provenance, enriched provenance carries endpoint/input parameters, and relaxed CLI runs still write experiment artifacts.
- Document the updated validation flow and schema-binding behavior in `docs/specs/synesthetic_labs_v0.3.6.md` once remediated.
