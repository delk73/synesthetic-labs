# Synesthetic Labs State Report (v0.3.6a)

## Summary of repo state

- CLI boots `.env`, normalizes LABS/Azure defaults, and honours `--engine` overrides before validation.
- External generators cache MCP schema metadata, bind Azure requests to strict JSON Schema, and parse completions strictly via `json.loads`.
- Structured logging emits JSONL entries with trace/schema/deployment fields while Gemini generation intentionally raises `NotImplementedError`.

## Alignment (Rule → Status → Evidence)

| Rule | Status | Evidence |
| --- | --- | --- |
| `env-preload-v0.3.6a` | Present | `labs/cli.py:20` loads `.env` via `load_dotenv` ahead of CLI setup.<br>`labs/cli.py:25` and `labs/cli.py:39` seed LABS defaults and enumerate required Azure keys for exposure warnings.<br>`labs/cli.py:209` routes `--engine` overrides into `build_external_generator`. |
| `mcp-schema-pull-v0.3.6a` | Present | `labs/generator/external.py:96` fetches `get_schema_from_mcp("synesthetic-asset", version=version)` with caching.<br>`labs/generator/external.py:104` persists the schema `$id` and MCP-reported `version` for downstream logging.<br>`tests/test_mcp_schema_pull.py:21` asserts the MCP payload is OK and exposes `schema["version"]`. |
| `gemini-placeholder-v0.3.6a` | Present | `labs/generator/external.py:1563` raises `NotImplementedError("Vertex AI structured-output unsupported")` in `GeminiGenerator.generate`.<br>`tests/test_external_generator.py:155` expects the placeholder exception when Gemini generation is invoked.<br>`tests/test_external_generator.py:152` constructs the generator in mock mode for the guard rail. |
| `azure-schema-binding-v0.3.6a` | Present | `labs/generator/external.py:2176` injects `response_format={"type": "json_schema", ... "strict": True}` built from the MCP descriptor.<br>`labs/generator/external.py:2184` captures the bound `schema_id`/`schema_version` metadata for logging.<br>`tests/test_external_generator.py:315` verifies the strict schema binding and cached identifiers in context. |
| `response-parse-v0.3.6a` | Present | `labs/generator/external.py:2080` reads the assistant message and `labs/generator/external.py:2099` parses the payload solely with `json.loads`.<br>`labs/generator/external.py:2101` raises `ExternalRequestError` on JSON decoding failures.<br>`tests/test_external_generator.py:395` and `tests/test_external_generator.py:398` confirm valid JSON passes while bad JSON triggers the error. |
| `validation-confirmation-v0.3.6a` | Present | `labs/cli.py:246` calls `invoke_mcp(asset, strict=strict_flag)` immediately after generation.<br>`labs/mcp/validate.py:146` returns the MCP validation result unchanged unless strict mode fails.<br>`tests/test_mcp.py:38` and `tests/test_mcp.py:40` assert `validate_asset` yields the pass-through success payload. |
| `error-handling-retry-v0.3.6a` | Present | `labs/generator/external.py:424` iterates attempts up to `self.max_retries` and captures attempt metadata.<br>`labs/generator/external.py:533` and `labs/generator/external.py:538` stop retrying when retries exhaust or the error is non-retryable.<br>`tests/test_external_generator.py:409` and `tests/test_external_generator.py:438` cover immediate 4xx failure versus 429 retry backoff success. |
| `structured-logging-v0.3.6a` | Present | `labs/logging.py:26` writes JSONL entries to `meta/output/labs/external.jsonl`.<br>`labs/generator/external.py:618` and `labs/generator/external.py:643` include engine, schema_id, schema_version, deployment, trace_id, and validation metadata in each record.<br>`tests/test_external_generator.py:112` and `tests/test_external_generator.py:134` assert those fields appear in the JSONL output. |

## Top gaps & fixes

- No behavioural gaps against v0.3.6a detected; continue monitoring upstream schema revisions so cached descriptors stay current.
- Capture a live `meta/output/labs/external.jsonl` sample once Azure credentials are configured to confirm telemetry across real deployments.

## Recommendations

- Add an integration test that runs `AzureOpenAIGenerator` against a mocked MCP validator to cover the strict validation handshake end-to-end.
- Expand the CLI quickstart in `README.md` with explicit Azure environment setup steps plus a Gemini placeholder callout for new operators.
