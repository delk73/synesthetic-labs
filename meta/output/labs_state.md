# Synesthetic Labs State Report (v0.3.6a)

## Summary of Repo State

- **Environment surfaces**: The CLI still omits several Azure env warnings—`AZURE_OPENAI_API_VERSION` never appears and `LABS_EXTERNAL_ENGINE` defaults silently—though dotenv loading now runs at import time.
- **External integrations**: Gemini generation is hard-disabled via `NotImplementedError`, while Azure chat completions use structured JSON responses with deterministic parsing and schema binding through MCP lookups.
- **Normalization & provenance**: Legacy (`0.7.3`) assets retain trimmed meta provenance instead of dropping it entirely, and the assembler still lacks a dedicated fallback filler helper.
- **Observability**: External run logs capture endpoint, schema binding, and validation data, but omit deployment identifiers, leaving audit trails incomplete.

## Alignment (Rule → Status → Evidence)

| Rule | Status | Evidence |
| --- | --- | --- |
| `env-preload-v0.3.6a` | Divergent | labs/cli.py:16-51 loads dotenv and seeds defaults but never surfaces `AZURE_OPENAI_API_VERSION` or reiterates `LABS_EXTERNAL_ENGINE`.<br>labs/cli.py:40-68 warn for engine-specific keys yet skip `AZURE_OPENAI_API_VERSION` and `LABS_EXTERNAL_LIVE` when unset.<br>requirements.txt:13 retains `python-dotenv`, confirming preload support while highlighting the missing Azure notices. |
| `mcp-schema-pull-v0.3.6a` | Present | labs/generator/external.py:24-133 caches `get_schema("synesthetic-asset", version=...)` and stores `schema_id` for normalization.<br>tests/test_mcp_schema_pull.py:12-44 asserts both `get_schema` and `list_schemas` succeed and return `ok`. |
| `gemini-placeholder-v0.3.6a` | Present | labs/generator/external.py:1493-1507 raises `NotImplementedError("Gemini structured-output is disabled until Vertex AI migration.")`.<br>tests/test_external_generator.py:151-160 expects `pytest.raises(NotImplementedError)` when `GeminiGenerator.generate()` is invoked. |
| `azure-schema-binding-v0.3.6a` | Present | labs/generator/external.py:1888-1967 builds chat-completion payloads with `response_format={'type': 'json_object'}` and stores live deployment info from `AZURE_OPENAI_*` env vars.<br>tests/test_external_generator.py:181-318 exercise Azure responses and assert `response_format` plus JSON decoding via `message.content`. |
| `response-parse-v0.3.6a` | Present | labs/generator/external.py:1742-1860 reads Gemini `candidates[0].content.parts` and falls back to deterministic JSON loads; OpenAI path decodes `choices[0].message.content`.<br>tests/test_external_generator.py:214-318 validate JSON parsing from `message.content` and Gemini normalization helpers. |
| `normalization-schema-0.7.3-v0.3.6a` | Divergent | labs/generator/assembler.py:335-372 retains `meta_info['provenance']` (engine/trace/timestamp) instead of omitting provenance for 0.7.3 payloads.<br>labs/generator/assembler.py:108-166 only offers `fill_defaults`—no `_fill_empty_sections` helper mentioned in the spec.<br>tests/test_generator.py:62-87 still assert `meta_info['provenance']['generator']`, locking in the extra metadata. |
| `provenance-enriched-schema-v0.3.6a` | Present | labs/generator/assembler.py:646-688 injects `engine`, `endpoint`, `deployment`, `api_version`, and `input_parameters` when schema ≥0.7.4.<br>tests/test_generator.py:12-39 confirm enriched assets expose generator agent/version and consistent trace IDs. |
| `cli-validation-flow-v0.3.6a` | Present | labs/cli.py:223-266 calls `invoke_mcp(asset, strict=strict_flag)` and records both critic-provided and local MCP responses.<br>tests/test_pipeline.py:19-120 cover strict success and relaxed-warning flows, asserting persistence and warning semantics. |
| `error-handling-retry-v0.3.6a` | Present | labs/generator/external.py:322-520 classifies HTTP errors, retries `>=500`/429 with capped exponential backoff, and logs attempts.<br>tests/test_external_generator.py:320-370 assert retries on 503 and immediate failure on 401/400 cases. |
| `structured-logging-v0.3.6a` | Divergent | labs/generator/external.py:573-636 writes external logs without a `deployment` field, despite capturing endpoint/schema binding.<br>tests/test_external_generator.py:200-240 read the log entry but never assert deployment presence, leaving the gap untested. |
| `validation-passes-v0.3.6a` | Present | labs/mcp/validate.py:146-166 enforces strict-mode failures via `invoke_mcp`, printing relaxed warnings otherwise.<br>tests/test_pipeline.py:19-118 show strict runs persisting assets and relaxed mode emitting warnings while still returning review payloads. |
| `fallback-filling-v0.3.6a` | Divergent | labs/generator/assembler.py:108-166 relies on generic `fill_defaults` rather than a dedicated `_fill_empty_sections` helper mandated by the spec.<br>tests/test_generator.py:62-87 expect populated sections indirectly but offer no coverage for explicit fallback behaviour. |

## Top Gaps & Fixes

1. **Broaden environment surfacing**: Expand `_load_env_file()` warnings to include `AZURE_OPENAI_API_VERSION`, `LABS_EXTERNAL_ENGINE`, and `LABS_EXTERNAL_LIVE` so operators see every required knob.
2. **Complete legacy normalization**: Introduce the `_fill_empty_sections` helper (or equivalent) and strip provenance entirely from 0.7.3 payloads to meet the legacy schema contract.
3. **Enrich external logging**: Add deployment metadata to `record_run()` outputs and assert it in tests to close the observability gap.

## Recommendations

- Add regression coverage ensuring Azure logs capture `deployment` and relaxed CLI runs persist experiment metadata as expected.
- Promote a reusable fallback filler utility shared between normalization paths to guarantee deterministic scaffolds.
- Extend environment self-check tests to assert presence/ordering of every Gemini and Azure credential surfaced at startup.
