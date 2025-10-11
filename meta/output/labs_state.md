# Synesthetic Labs State Report (v0.3.6a)

## Summary of repo state

- CLI bootstraps `.env`, sets schema defaults, and surfaces Azure/Gemini env gaps during import.
- MCP schema descriptors are cached once and reused across Azure/Gemini pathways, keeping schema_id + version in context.
- External generators now bind Azure Chat Completions to the MCP schema with strict JSON parsing, while Gemini remains a guarded placeholder.

## Alignment (Rule → Status → Evidence)

| Rule | Status | Evidence |
| --- | --- | --- |
| `env-preload-v0.3.6a` | Present | `labs/cli.py::_load_env_file` loads dotenv, seeds LABS_* defaults, and warns when Azure vars are missing.<br>`requirements.txt` pins `python-dotenv==1.1.1`. |
| `mcp-schema-pull-v0.3.6a` | Present | `_cached_schema_descriptor` in `labs/generator/external.py` calls `get_schema("synesthetic-asset", version=...)`, caching `(schema_id, version, schema)`.<br>`tests/test_mcp_schema_pull.py::test_mcp_schema_pull` asserts the schema+id tuple succeeds. |
| `gemini-placeholder-v0.3.6a` | Present | `GeminiGenerator.generate` raises `NotImplementedError("Vertex AI structured-output unsupported")`.<br>`tests/test_external_generator.py::test_gemini_generate_is_placeholder` checks the exact message. |
| `azure-schema-binding-v0.3.6a` | Present | `AzureOpenAIGenerator._build_request` sets `response_format` to `json_schema` with the fetched MCP schema and `strict: True`.<br>`tests/test_external_generator.py::test_azure_schema_binding` verifies schema binding metadata on the request context. |
| `response-parse-v0.3.6a` | Present | `OpenAIGenerator._extract_structured_payload` parses `response.choices[0].message.content` via `json.loads` and raises on decode errors.<br>`tests/test_external_generator.py::test_openai_strict_parse` confirms good JSON passes and invalid JSON raises `ExternalRequestError`. |
| `validation-confirmation-v0.3.6a` | Present | `labs/cli.py::main` invokes `invoke_mcp(asset, strict=strict_flag)` after generation without mutating the asset.<br>`labs/mcp/validate.py::invoke_mcp` returns the result and only raises for strict failures. |
| `error-handling-retry-v0.3.6a` | Present | `ExternalGenerator.generate` backs off up to three attempts, recording retry metadata and aborting on non-retryable 4xx errors.<br>`tests/test_external_generator.py` exercises 400 vs 503 flows to cover fail-fast vs retry. |
| `structured-logging-v0.3.6a` | Present | `ExternalGenerator.record_run` writes engine, schema_id, schema_version, deployment, trace_id, and validation_status to the log record.<br>`tests/test_external_generator.py::test_gemini_generator_normalises_asset` inspects the JSONL output for those fields. |

## Top gaps & fixes

- No spec divergences detected; keep monitoring external schema updates to ensure descriptors stay current.
- Capture a fresh live `external.jsonl` sample once Azure credentials are configured to validate production telemetry.

## Recommendations

- Add integration coverage that exercises `AzureOpenAIGenerator` against a mocked MCP validator with `strict=True` to assert the end-to-end handshake.
- Extend CLI docs in `README.md` with a quickstart for setting Azure env vars plus Gemini placeholders for clarity.
