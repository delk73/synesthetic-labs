# Synesthetic Labs State Report (v0.3.6a)

## Summary of repo state

- CLI preloads `.env`, seeds LABS defaults at 0.7.3, warns when Azure/Gemini keys are missing, and honours `--engine` overrides during generation.
- External generators cache MCP schema descriptors, bind Azure requests to strict `json_schema` payloads, and parse completions exclusively via `json.loads`.
- Structured logging records engine/deployment/schema metadata for every run while Gemini generation remains an intentional `NotImplementedError`.

## Alignment (Rule → Status → Evidence)

| Rule | Status | Evidence |
| --- | --- | --- |
| `env-preload-v0.3.6a` | Present | `labs/cli.py:16` uses `load_dotenv`, seeds LABS/AZURE defaults, and warns when required env vars are absent.<br>`requirements.txt:4` pins `python-dotenv==1.1.1` for CLI env bootstrapping. |
| `mcp-schema-pull-v0.3.6a` | Present | `_cached_schema_descriptor` at `labs/generator/external.py:93` calls `get_schema("synesthetic-asset", version=...)` and caches `(schema_id, version, schema)`.<br>`tests/test_mcp_schema_pull.py:4` exercises `get_schema` and asserts an OK response with structural checks. |
| `gemini-placeholder-v0.3.6a` | Present | `labs/generator/external.py:1496` has `GeminiGenerator.generate` raising `NotImplementedError("Vertex AI structured-output unsupported")`.<br>`tests/test_external_generator.py:152` asserts the exact placeholder exception. |
| `azure-schema-binding-v0.3.6a` | Present | `labs/generator/external.py:2114` injects `response_format={"type": "json_schema", "strict": True, ...}` using the MCP schema descriptor.<br>`tests/test_external_generator.py:311` verifies the Azure context includes the strict schema binding metadata. |
| `response-parse-v0.3.6a` | Present | `labs/generator/external.py:2026` loads `response.choices[0].message.content` via `json.loads`, raising on decode errors.<br>`tests/test_external_generator.py:371` covers valid vs invalid JSON to confirm strict parsing. |
| `validation-confirmation-v0.3.6a` | Present | `labs/cli.py:246` calls `invoke_mcp(asset, strict=strict_flag)` immediately after generation.<br>`labs/mcp/validate.py:141` returns the validation result untouched and only raises when strict mode fails. |
| `error-handling-retry-v0.3.6a` | Present | `labs/generator/external.py:423` retries up to three attempts and stops when an error is non-retryable.<br>`tests/test_external_generator.py:402` and `tests/test_external_generator.py:419` cover fail-fast auth errors and 429 retry backoff success. |
| `structured-logging-v0.3.6a` | Present | `labs/generator/external.py:585` records engine, deployment, schema_id/version, trace_id, and validation_status in the JSONL entry.<br>`tests/test_external_generator.py:104` asserts the log captures those fields for a Gemini run. |

## Top gaps & fixes

- No spec gaps detected; continue watching upstream 0.7.x schema updates so cached descriptors stay fresh.
- Capture a live `external.jsonl` sample once Azure credentials are configured to validate production telemetry fields.

## Recommendations

- Add an integration test that runs `AzureOpenAIGenerator` through a mocked MCP validator to cover the strict-mode handshake end-to-end.
- Expand the CLI quickstart in `README.md` with explicit Azure env setup steps and a Gemini placeholder callout for clarity.
