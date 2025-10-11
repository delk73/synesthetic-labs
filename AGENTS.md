# Synesthetic Labs State Report (v0.3.6a)

## Summary of repo state

- **Environment surfacing**: `.env` loading in the CLI keeps schema and engine toggles front-and-centre while warning when Azure credentials are missing.
- **Schema plumbing**: MCP schemas are fetched and cached (with `schema_id`), yet Azure calls never bind them and the Gemini placeholder message drifts from the mandated text.
- **Response contract**: Regex fallbacks remain in the OpenAI/Azure parsing path, so strict MCP validation still fails despite detailed logging.

## Alignment (Rule → Status → Evidence)

| Rule | Status | Evidence |
| --- | --- | --- |
| `env-preload-v0.3.6a` | Present | `labs/cli.py` imports `load_dotenv`, seeds `LABS_SCHEMA_VERSION`/`LABS_FAIL_FAST` defaults, and logs missing engine variables during module import.<br>`requirements.txt` pins `python-dotenv==1.1.1`, ensuring the preload helper remains available. |
| `mcp-schema-pull-v0.3.6a` | Present | `_cached_schema_descriptor` in `labs/generator/external.py` invokes `get_schema("synesthetic-asset", version=...)` and caches `(schema_id, version, schema)`.<br>`tests/test_mcp_schema_pull.py::test_mcp_schema_pull` asserts both schema listing and retrieval succeed. |
| `gemini-placeholder-v0.3.6a` | Divergent | `GeminiGenerator.generate` raises `NotImplementedError("Gemini structured-output is disabled until Vertex AI migration.")`, not the spec-required "Vertex AI structured-output unsupported".<br>`tests/test_external_generator.py::test_gemini_generate_is_placeholder` only checks the exception type, leaving the message drift untested. |
| `azure-schema-binding-v0.3.6a` | Divergent | `AzureOpenAIGenerator` inherits `_build_request` with `response_format={"type": "json_object"}` and never attaches the MCP schema nor `strict=True`.<br>No regression in `tests/test_external_generator.py` verifies the schema binding contract. |
| `response-parse-v0.3.6a` | Divergent | `_extract_structured_payload` falls back to `re.search("{.*}")` when `json.loads` fails, so parsing isn’t deterministic.<br>`tests/test_external_generator.py` covers the fallback path instead of enforcing pure `json.loads(message.content)`. |
| `validation-confirmation-v0.3.6a` | Present | `labs/mcp/validate.invoke_mcp` returns the validation payload and raises only when `strict=True` and `ok` is false, leaving the asset untouched.<br>`labs/cli.py::main` calls `invoke_mcp(asset, strict=strict_flag)` after generation, matching the confirmation-only flow. |
| `error-handling-retry-v0.3.6a` | Present | The retry loop in `ExternalGenerator.generate` backs off up to `max_retries`, while `_classify_http_error` marks 5xx/429 as retryable and 4xx as fatal.<br>`tests/test_external_generator.py` includes retry vs fail-fast assertions for 503 and 400 responses. |
| `structured-logging-v0.3.6a` | Present | `ExternalGenerator.record_run` writes `engine`, `schema_id`, `schema_version`, `deployment`, `trace_id`, and `validation_status` to `external.jsonl`.<br>`meta/output/labs/external.jsonl` trace `0b96a96f-15cc-437b-acae-b779b5f60e9d` shows those fields in practice. |

## Top gaps & fixes

1. Match the Gemini placeholder message to "Vertex AI structured-output unsupported" and assert it in unit tests.
2. Bind Azure Chat Completions to the MCP schema (`response_format.type == 'json_schema'`, embed schema, set `strict=True`) and add coverage.
3. Remove regex fallbacks in `_extract_structured_payload` so responses rely solely on `json.loads` of `message.content`.

## Recommendations

- Tighten Azure mock outputs to match schema 0.7.3 exactly and validate them via `invoke_mcp(..., strict=True)` in tests.
- Capture a fresh structured log sample once Azure binding is fixed to document the compliant fields.
- Strip legacy provenance/control enrichment from 0.7.3 assets to keep MCP validation noise-free.
