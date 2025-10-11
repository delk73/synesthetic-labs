# Synesthetic Labs State Report (v0.3.6a)

## Summary of repo state

- CLI import bootstraps `.env`, pins schema defaults at 0.7.3, and warns when Azure/Gemini vars are missing.
- External generators cache the MCP descriptor once, reuse schema_id/version, and inject strict JSON schema bindings for Azure Chat Completions.
- Gemini remains a guarded placeholder while structured logging persists engine, schema, and validation metadata for every run.

## Alignment (Rule → Status → Evidence)

| Rule | Status | Evidence |
| --- | --- | --- |
| `env-preload-v0.3.6a` | Present | `labs/cli.py::_load_env_file` loads dotenv, seeds LABS_* defaults, and surfaces missing Azure keys via warnings.<br>`requirements.txt` pins `python-dotenv==1.1.1`. |
| `mcp-schema-pull-v0.3.6a` | Present | `_cached_schema_descriptor` in `labs/generator/external.py` pulls `get_schema("synesthetic-asset", version=...)` and caches `(schema_id, version, schema)`.<br>`tests/test_mcp_schema_pull.py::test_mcp_schema_pull` exercises the core import and asserts an OK response. |
| `gemini-placeholder-v0.3.6a` | Present | `GeminiGenerator.generate` unconditionally raises `NotImplementedError("Vertex AI structured-output unsupported")`.<br>`tests/test_external_generator.py::test_gemini_generate_is_placeholder` asserts the exact message. |
| `azure-schema-binding-v0.3.6a` | Present | `AzureOpenAIGenerator._build_request` sets `response_format` to `json_schema` with the loaded MCP schema and `strict: True`.<br>`tests/test_external_generator.py::test_azure_schema_binding` inspects the bound schema metadata in the request context. |
| `response-parse-v0.3.6a` | Present | `OpenAIGenerator._extract_structured_payload` parses `response.choices[0].message.content` exclusively via `json.loads` and raises on decode errors.<br>`tests/test_external_generator.py::test_openai_strict_parse` covers good vs bad JSON paths. |
| `validation-confirmation-v0.3.6a` | Present | `labs/cli.py::main` calls `invoke_mcp(asset, strict=strict_flag)` immediately after generation.<br>`labs/mcp/validate.py::invoke_mcp` returns the result unchanged and only raises when strict mode fails. |
| `error-handling-retry-v0.3.6a` | Present | `ExternalGenerator.generate` backs off up to three attempts, logging attempt metadata and aborting on non-retryable 4xx errors.<br>`tests/test_external_generator.py::test_no_retry_on_auth_error` vs `::test_rate_limited_retries` cover fail-fast 401/429 handling. |
| `structured-logging-v0.3.6a` | Present | `ExternalGenerator.record_run` writes engine, deployment, schema_id/version, trace_id, and validation_status into the JSONL payload.<br>`tests/test_external_generator.py::test_gemini_generator_normalises_asset` reads the log and asserts those fields. |

## Top gaps & fixes

- No spec gaps observed; continue monitoring upstream schema revisions for 0.7.x to refresh cached descriptors promptly.
- Capture a live `external.jsonl` sample once Azure credentials are configured to validate production telemetry.

## Recommendations

- Add an integration test that wires `AzureOpenAIGenerator` through a mocked MCP validator in strict mode to cover the full handshake.
- Expand the CLI quickstart in `README.md` with explicit Azure env setup and a Gemini placeholder callout for clarity.
