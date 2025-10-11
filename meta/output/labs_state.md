# Synesthetic Labs State Report (v0.3.6a)

## Summary of repo state

- **Environment surfacing**: The CLI still preloads `.env`, defaulting schema/engine toggles and warning for missing Azure credentials, so operators see all required knobs up front.
- **Schema plumbing**: Generators cache MCP schemas (`schema_id`, `schema_version`) correctly, but Azure requests never bind them and Gemini’s placeholder message diverges from the spec text.
- **Response contract**: External parsers keep regex fallbacks and legacy enrichment, causing strict MCP validation failures despite robust logging of each attempt.

## Alignment (Rule → Status → Evidence)

| Rule | Status | Evidence |
| --- | --- | --- |
| `env-preload-v0.3.6a` | Present | `labs/cli.py` loads `.env`, seeds `LABS_SCHEMA_VERSION`/`LABS_FAIL_FAST`, and logs missing engine vars right after import.<br>`labs/cli.py` enumerates Azure keys (`AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_DEPLOYMENT`, `AZURE_OPENAI_API_VERSION`) per engine.<br>`requirements.txt` keeps `python-dotenv==1.1.1` so the preload path stays wired. |
| `mcp-schema-pull-v0.3.6a` | Present | `_cached_schema_descriptor` in `labs/generator/external.py` calls `get_schema("synesthetic-asset", version=...)`, returning `(schema_id, version, schema)` for downstream use.<br>`tests/test_mcp_schema_pull.py::test_mcp_schema_pull` asserts both `list_schemas()` and `get_schema()` report `ok`. |
| `gemini-placeholder-v0.3.6a` | Divergent | `GeminiGenerator.generate` raises `NotImplementedError("Gemini structured-output is disabled until Vertex AI migration.")`, not the required "Vertex AI structured-output unsupported" string.<br>`tests/test_external_generator.py::test_gemini_generate_is_placeholder` only checks the exception type, so the spec-required message isn’t enforced. |
| `azure-schema-binding-v0.3.6a` | Divergent | `AzureOpenAIGenerator` inherits `_build_request` with `response_format={"type": "json_object"}` and never adds `json_schema`/`strict=True`.<br>No Azure-specific test (`tests/test_external_generator.py`) asserts schema binding, allowing the drift to persist. |
| `response-parse-v0.3.6a` | Divergent | `_extract_structured_payload` in `OpenAIGenerator` falls back to `re.search(r"\{.*\}")` when `json.loads` fails, violating the deterministic parse requirement.<br>`tests/test_external_generator.py::test_openai_regex_fallback` (section covering `_extract_structured_payload`) exercises that regex path instead of forbidding it. |
| `validation-confirmation-v0.3.6a` | Present | `labs/mcp/validate.invoke_mcp` returns the validation result and only raises when `strict` and `ok` is false, leaving the asset untouched.<br>`labs/cli.py::main` routes generator output through `invoke_mcp(..., strict=strict_flag)` to confirm validation post-generation. |
| `error-handling-retry-v0.3.6a` | Present | `ExternalGenerator.generate` retries up to `max_retries` with exponential backoff, while `_classify_http_error` flags 5xx/429 as retryable and 4xx as fatal.<br>`tests/test_external_generator.py::test_external_generator_logs_failure_when_transport_errors` and sibling retry cases cover the 400 vs 503 handling split. |
| `structured-logging-v0.3.6a` | Present | `ExternalGenerator.record_run` writes JSONL entries with `engine`, `schema_id`, `schema_version`, `deployment`, `trace_id`, and `validation_status`.<br>`meta/output/labs/external.jsonl` entries (e.g. trace `0b96a96f-15cc-437b-acae-b779b5f60e9d`) include those fields, confirming the structured log contract. |

## Top gaps & fixes

1. **Normalize the Gemini placeholder message** to match the spec literal "Vertex AI structured-output unsupported" and add an assertion for the string in unit tests.
2. **Bind Azure chat completions to the MCP schema** by supplying `response_format.type == 'json_schema'`, embedding the fetched schema, and setting `strict=True`, alongside regression coverage.
3. **Drop regex fallbacks in `_extract_structured_payload`** so responses are parsed strictly via `json.loads(response.choices[0].message.content)` with tests enforcing the contract.

## Recommendations

- Extend the Azure mock path to emit schema-compliant 0.7.3 assets and verify them with `invoke_mcp(..., strict=True)` in tests.
- Capture a golden Azure success log once schema binding is restored to track `schema_binding=True` in observability dashboards.
- Prune legacy provenance/control enrichments in mock outputs to reduce MCP validation noise and keep assets lean under schema 0.7.3.
