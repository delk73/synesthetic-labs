# Synesthetic Labs State Report (v0.3.6a)

## Summary of repo state

- CLI preloads `.env`, seeds LABS defaults at 0.7.3, warns when Azure/Gemini keys are missing, and honours `--engine` overrides during generation.
- External generators cache MCP schema descriptors, bind Azure requests to strict `json_schema` payloads, and parse completions exclusively via `json.loads`.
- Structured logging records engine/deployment/schema metadata for every run while Gemini generation remains an intentional `NotImplementedError`.

## Alignment (Rule → Status → Evidence)

| Rule | Status | Evidence |
| --- | --- | --- |
| `env-preload-v0.3.6a` | Present | `labs/cli.py:20` preloads `.env` via `load_dotenv` before CLI setup.<br>`labs/cli.py:25` seeds `LABS_*` defaults and Azure fallbacks while `labs/cli.py:209` routes `--engine` overrides through `build_external_generator`.<br>`requirements.txt:4` pins `python-dotenv==1.1.1` for CLI env bootstrapping. |
| `mcp-schema-pull-v0.3.6a` | Present | `labs/generator/external.py:96` fetches `get_schema_from_mcp("synesthetic-asset", version=version)` and caches the response.<br>`labs/generator/external.py:104` stores the schema `$id` and MCP-reported `version` for downstream logging.<br>`tests/test_mcp_schema_pull.py:21` exercises `get_schema` and asserts an OK schema payload. |
| `gemini-placeholder-v0.3.6a` | Present | `labs/generator/external.py:1563` raises `NotImplementedError("Vertex AI structured-output unsupported")` in `GeminiGenerator.generate`.<br>`tests/test_external_generator.py:155` expects the placeholder exception when Gemini generation is invoked. |
| `azure-schema-binding-v0.3.6a` | Present | `labs/generator/external.py:2176` builds `response_format={"type": "json_schema", "json_schema": {..., "strict": True}}` from the MCP descriptor.<br>`labs/generator/external.py:2184` records the bound `schema_id`/`schema_version` metadata for logging.<br>`tests/test_external_generator.py:315` confirms the Azure generator context carries the strict schema binding. |
| `response-parse-v0.3.6a` | Present | `labs/generator/external.py:2099` parses `response.choices[0].message.content` strictly with `json.loads` and rejects decode errors.<br>`tests/test_external_generator.py:395` verifies valid JSON succeeds while bad JSON raises `ExternalRequestError`. |
| `validation-confirmation-v0.3.6a` | Present | `labs/cli.py:246` calls `invoke_mcp(asset, strict=strict_flag)` immediately after generation.<br>`labs/mcp/validate.py:151` returns the validation result unchanged and raises only when strict mode fails.<br>`tests/test_mcp.py:40` asserts `validate_asset` returns the pass-through payload used by CLI validation. |
| `error-handling-retry-v0.3.6a` | Present | `labs/generator/external.py:424` iterates attempts up to `self.max_retries` per request.<br>`labs/generator/external.py:538` stops retrying once retries are exhausted or the error is non-retryable.<br>`tests/test_external_generator.py:409` and `tests/test_external_generator.py:438` cover fail-fast auth errors and 429 retry backoff success. |
| `structured-logging-v0.3.6a` | Present | `labs/generator/external.py:618` writes engine, prompt, schema_version, and validation data into the log record.<br>`labs/generator/external.py:640` captures `schema_id`, `schema_binding_version`, `endpoint`, and `deployment` for telemetry.<br>`tests/test_external_generator.py:112` asserts the JSONL entry includes engine, schema metadata, deployment, and validation status. |

## Top gaps & fixes

- No spec gaps detected; continue watching upstream 0.7.x schema updates so cached descriptors stay fresh.
- Capture a live `external.jsonl` sample once Azure credentials are configured to validate production telemetry fields.

## Recommendations

- Add an integration test that runs `AzureOpenAIGenerator` through a mocked MCP validator to cover the strict-mode handshake end-to-end.
- Expand the CLI quickstart in `README.md` with explicit Azure env setup steps and a Gemini placeholder callout for clarity.
