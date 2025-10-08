# Synesthetic Labs State Report (v0.3.5a)

## Summary of repo state

Environment bootstrapping and schema retrieval align with v0.3.5a, but Gemini schema binding, structured logging, and CLI-driven MCP validation still trail the spec; enriched assets also lack the full provenance payload now required for 0.7.4+ schemas.

## Alignment

| Rule | Status | Evidence |
| --- | --- | --- |
| `env-preload-v0.3.5a` | Present | `labs/cli.py` preloads the project `.env` via `load_dotenv` and seeds defaults for `GEMINI_MODEL`, `LABS_FAIL_FAST`, and `LABS_SCHEMA_VERSION`.<br>`labs/cli.py` immediately checks for `GEMINI_API_KEY`/`LABS_EXTERNAL_LIVE` and warns when unset.<br>`requirements.txt` pins `python-dotenv==1.1.1` to guarantee availability. |
| `external-live-toggle-v0.3.5a` | Present | `ExternalGenerator.__init__` derives `mock_mode` from `LABS_EXTERNAL_LIVE`, disabling live calls by default.<br>`labs/cli.py` surfaces missing `LABS_EXTERNAL_LIVE` at startup so operators know when live mode is unavailable.<br>`.env.example` documents `LABS_EXTERNAL_LIVE=1` for opt-in live execution. |
| `mcp-schema-pull-v0.3.5a` | Present | `labs/generator/external.py::_cached_schema_descriptor` calls `get_schema("synesthetic-asset", version=version)` and validates the response.<br>The returned payload seeds `_build_schema_skeleton` and the `$schema` URL before normalization.<br>`tests/test_mcp_schema_pull.py` exercises both `list_schemas()` and `get_schema()` against MCP. |
| `gemini-schema-binding-v0.3.5a` | Missing | `GeminiGenerator._build_request` only sets `generationConfig` to `{"responseMimeType": "application/json"}`—no `responseSchema` is included.<br>`record_run` writes external logs without a `schema_binding` flag or schema `$id` reference.<br>`tests/test_external_generator.py` lacks coverage for schema binding, mirroring the absent implementation. |
| `gemini-request-structure-v0.3.5a` | Present | `GeminiGenerator._build_request` wraps prompts under `contents -> parts -> text` as required.<br>`generationConfig` explicitly sets `responseMimeType` to `application/json`.<br>`tests/test_external_generator.py::test_gemini_build_request_injects_response_mime_type` confirms the structure. |
| `gemini-response-parse-v0.3.5a` | Present | `_parse_response` extracts `response["candidates"][0]["content"]["parts"][0]["text"]` and feeds it through `json.loads`.<br>Parsed data is merged into a schema-driven skeleton before normalization.<br>`tests/test_external_generator.py` asserts normalization uses the candidates/parts JSON payload. |
| `normalization-schema-0.7.3-v0.3.5a` | Present | `AssetAssembler.generate` routes `schema_version` starting with `0.7.3` through `_build_legacy_asset`.<br>`_build_legacy_asset` injects `$schema` and strips enriched-only fields so legacy payloads stay lean.<br>`AssetAssembler._normalize_0_7_3` prunes provenance, modulations, and extra parameters per spec. |
| `normalization-enriched-schema-v0.3.5a` | Divergent | `AssetAssembler._build_enriched_asset` emits `$schema` and provenance but `_build_asset_provenance` lacks `endpoint` and `input_parameters` keys.<br>`GeneratorAgent.propose` augments provenance with agent metadata yet omits endpoint/input_parameters for 0.7.4+.<br>`tests/test_generator.py` validates trace IDs but never asserts the missing provenance fields, confirming the gap. |
| `error-handling-retry-v0.3.5a` | Present | `ExternalGenerator.generate` retries while `ExternalRequestError.retryable` is `True`, using exponential backoff.<br>`_classify_http_error` marks `>=500` responses retryable and 4xx (auth) as terminal.<br>`tests/test_external_generator.py` covers both retrying (rate limit) and no-retry (auth error) scenarios. |
| `structured-logging-v0.3.5a` | Divergent | Logging still routes through `log_external_generation` instead of the spec's `log_event` API.<br>`record_run` omits required fields such as `endpoint` and `schema_binding` in `external.jsonl` entries.<br>`labs/logging.py` defines only `log_jsonl`/`log_external_generation`, so the standardized logger is absent. |
| `mcp-validation-flow-v0.3.5a` | Missing | `labs/cli.py` never imports or calls `invoke_mcp`, relying solely on `CriticAgent` for validation.<br>`_build_validator_optional` wraps `build_validator_from_env` but doesn't expose CLI `--strict/--relaxed` choices to an MCP invocation primitive.<br>No `tests/test_cli.py` exists to assert strict vs relaxed CLI flows. |
| `mcp-version-aware-validator-v0.3.5a` | Present | `_resolve_schema_path` extracts version strings with `re.search` and probes `meta/schemas/<version>/<filename>`.<br>If the versioned file is absent it falls back to an unversioned candidate before failing.<br>`tests/test_mcp_validator.py` locks in the expected 0.7.3/0.7.4 path resolution. |

## Top gaps & fixes

1. **Implement Gemini schema binding & logging parity:** Extend `GeminiGenerator._build_request` to attach `generationConfig.responseSchema` from `get_schema(...)["schema"]["$id"]`, and log `schema_binding: true` via the standardized logger.
2. **Wire CLI throughput to MCP validation contracts:** Introduce `invoke_mcp` plumbing in `labs/cli.py` (with strict/relaxed handling) and backfill `tests/test_cli.py` to exercise the modes.
3. **Enrich provenance for 0.7.4+ assets:** Update `AssetAssembler`/`GeneratorAgent` to include endpoint and input parameter details so enriched provenance meets the spec.

## Recommendations

* Align external logging with the spec by replacing `log_external_generation` calls with `log_event` (or upgrading the helper) and ensure `schema_binding`, `endpoint`, and taxonomy metadata are consistently emitted.
* Finish the CLI-to-MCP integration so operators can rely on `--strict/--relaxed` while still calling a concrete `invoke_mcp` implementation before persistence.
* Expand provenance builders for enriched schemas to capture engine, endpoint, trace_id, and structured `input_parameters`, then extend tests to pin the contract.
