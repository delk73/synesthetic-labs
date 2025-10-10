# Synesthetic Labs State Report (v0.3.6a)

## Summary of Repo State

- **Environment & configuration**: `.env` preloading is wired through `python-dotenv`, yet the CLI only surfaces Gemini settings—Azure OpenAI knobs and `LABS_EXTERNAL_ENGINE` still fly under the radar.
- **External contracts**: MCP schema retrieval succeeds, but the Gemini generator remains fully enabled (no placeholder/NotImplemented guard), Azure chat-completions support is absent, and parsing still relies on deprecated `function_call` branches.
- **Normalization & provenance**: Legacy (`0.7.3`) assets retain provenance and lack default section backfill, while enriched outputs omit endpoint/deployment/input parameter fields required by the provenance spec.
- **Lifecycle & logging**: Retry logic and structured logging largely function, but `invoke_mcp` never runs, relaxed CLI runs skip persistence, and external logs omit deployment metadata.

## Alignment

| Rule | Status | Evidence |
| --- | --- | --- |
| `env-preload-v0.3.6a` | Divergent | `labs/cli.py`: `_load_env_file()` seeds defaults for `LABS_SCHEMA_VERSION`, `LABS_FAIL_FAST`, and `GEMINI_MODEL`, yet never references `LABS_EXTERNAL_ENGINE` or any `AZURE_OPENAI_*` variables.<br>`labs/cli.py`: the warning loop only covers `GEMINI_API_KEY` and `LABS_EXTERNAL_LIVE`, leaving Azure credentials silent.<br>`requirements.txt`: `python-dotenv==1.1.1` confirms env preload support, underscoring the missing Azure visibility. |
| `mcp-schema-pull-v0.3.6a` | Present | `labs/generator/external.py`: `_cached_schema_descriptor()` wraps `get_schema("synesthetic-asset", version=...)` and returns `(schema_id, version, schema)`.<br>`tests/test_mcp_schema_pull.py`: `test_mcp_schema_pull` asserts both `get_schema` and `list_schemas` return `ok`. |
| `gemini-placeholder-v0.3.6a` | Missing | `labs/generator/external.py`: `GeminiGenerator.generate()` executes the full request/parse pipeline instead of raising `NotImplementedError` when invoked.<br>`labs/generator/external.py`: the class contains no "structured output disabled" warning mentioning Vertex AI.<br>`tests/test_external_generator.py`: there is no `pytest.raises(NotImplementedError)` coverage for Gemini. |
| `azure-schema-binding-v0.3.6a` | Missing | `labs/generator/external.py`: the codebase only defines `OpenAIGenerator` pointing at `https://api.openai.com/v1/chat/completions` and reading `OPENAI_*` env vars.<br>`labs/generator/external.py`: no references to `AZURE_OPENAI_DEPLOYMENT`, `response_format`, or `json_object` appear in the file.<br>`tests/test_external_generator.py`: suite lacks any `AzureOpenAI`/`json_object` assertions. |
| `response-parse-v0.3.6a` | Divergent | `labs/generator/external.py`: `GeminiGenerator._parse_response()` prefers `function_call` payloads instead of deterministically reading `candidates[0].content.parts[0].text`.<br>`labs/generator/external.py`: `OpenAIGenerator._parse_response()` reads `response["asset"]` and never decodes `response.choices[0].message.content` JSON.<br>`tests/test_external_generator.py`: no test covers JSON decoding from `message.content`. |
| `normalization-schema-0.7.3-v0.3.6a` | Divergent | `labs/generator/assembler.py`: `_normalize_0_7_3()` copies `meta_info["provenance"]` into the legacy asset despite the omission requirement.<br>`labs/generator/assembler.py`: there is no `_fill_empty_sections` call, so shader/tone/haptic/control scaffolds are not backfilled.<br>`tests/test_generator.py`: legacy assertions still expect `meta_info["provenance"]["generator"]`. |
| `provenance-enriched-schema-v0.3.6a` | Divergent | `labs/generator/assembler.py`: `_build_asset_provenance()` omits `endpoint`, `deployment`, `api_version`, and `input_parameters` fields.<br>`labs/generator/external.py`: `_make_provenance_block()` adds endpoint/input parameters only for external engines, leaving assembler outputs under-specified.<br>`tests/test_generator.py`: enriched tests merely check provenance exists, not that required fields are populated. |
| `cli-validation-flow-v0.3.6a` | Missing | `labs/cli.py`: the generate command never calls an `invoke_mcp(asset, strict=...)` helper—validation flows solely through `CriticAgent.review()`.<br>`tests/test_cli.py`: no coverage exists for strict/relaxed CLI flags invoking an MCP stub. |
| `error-handling-retry-v0.3.6a` | Present | `labs/generator/external.py`: `_classify_http_error()` retries `429`/`5xx` and fails fast on `401`/`403`.<br>`labs/generator/external.py`: `_compute_backoff()` enforces capped exponential backoff with jitter.<br>`tests/test_external_generator.py`: `test_rate_limited_retries` and `test_no_retry_on_auth_error` confirm the behaviour. |
| `structured-logging-v0.3.6a` | Divergent | `labs/generator/external.py`: `record_run()` omits a `deployment` field even when logging live runs.<br>`labs/logging.py`: `log_external_generation()` simply writes the record, so missing deployment metadata hits disk.<br>`tests/test_external_generator.py`: log assertions never require deployment metadata. |
| `validation-passes-v0.3.6a` | Divergent | `labs/cli.py`: `_persist_asset()` runs only when `_review_mcp_ok(review)` is true, so relaxed failures skip persistence.<br>`tests/test_pipeline.py`: `test_cli_generate_relaxed_mode_warns_validation` asserts `experiment_path` remains `None` in relaxed mode.<br>`labs/mcp/validate.py`: lacks `invoke_mcp`, leaving strict validation to Critic heuristics. |
| `fallback-filling-v0.3.6a` | Missing | `labs/generator/assembler.py`: no `_fill_empty_sections` helper exists and section builders copy generator output verbatim.<br>`labs/generator/assembler.py`: legacy normalization never touches `AssetAssembler.default_*` utilities.<br>`tests/test_generator.py`: no test asserts empty sections are auto-filled. |

## Top gaps & fixes

1. **Broaden environment surfacing**: Extend `_load_env_file()`/warning loops to include `LABS_EXTERNAL_ENGINE` and every `AZURE_OPENAI_*` variable alongside the Gemini keys.
2. **Implement external placeholders & Azure contract**: Gate `GeminiGenerator` behind a clear NotImplemented placeholder and introduce an Azure chat-completions client with `response_format={'type':'json_object'}` and deterministic parsing.
3. **Fix parsing & provenance**: Make Gemini parsing deterministic, teach OpenAI/Azure to decode `choices[0].message.content`, and enrich provenance with endpoint, deployment, api_version, and input parameters.
4. **Normalize legacy assets & lifecycle**: Add deterministic section fillers for 0.7.3 assets, wire in `invoke_mcp()` for CLI strict/relaxed flows (persisting relaxed runs), and log deployment metadata for external executions.

## Recommendations

- Author regression tests for the Gemini placeholder path, Azure chat payload/response flow, and deterministic parsing of `message.content`.
- Expand assembler tests to assert legacy assets omit provenance, enriched assets include endpoint/deployment/input parameters, and fallback fillers populate empty sections.
- Extend CLI/logging coverage to verify `invoke_mcp` usage, relaxed-mode persistence, and deployment metadata in `external.jsonl`.
