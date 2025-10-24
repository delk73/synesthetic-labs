# Synesthetic Labs State Report (v0.3.6a)

## Summary of repo state

- CLI bootstrap now preloads `.env`, locks `LABS_SCHEMA_VERSION` to `0.7.3`, and forces `LABS_SCHEMA_RESOLUTION="inline"` before agents start (`labs/cli.py:18`, `labs/cli.py:24`).
- Shared MCP client defaults to inline resolution, so cached descriptors embed `$ref` dependencies and Azure bindings inherit the embedded schema bundle (`labs/mcp/client.py:60`, `labs/mcp/client.py:109`, `labs/generator/external.py:101`).
- External generator telemetry records inline schema metadata, and tests cover Azure binding, Gemini guard rails, strict parsing, and inline propagation end-to-end (`labs/generator/external.py:421`, `labs/generator/external.py:653`, `tests/test_external_generator.py:331`, `tests/test_labs_mcp_modes.py:48`).

## Alignment (Rule → Status → Evidence)

| Rule | Status | Evidence |
| --- | --- | --- |
| `env-preload-v0.3.6a` | Present | `labs/cli.py:18` loads `.env` on startup.<br>`labs/cli.py:24` sets defaults for `LABS_SCHEMA_VERSION`, `LABS_SCHEMA_RESOLUTION="inline"`, and other engine vars.<br>`labs/cli.py:165` keeps the CLI `--engine` override above env settings. |
| `mcp-schema-fetch-inline-v0.3.6a` | Present | `labs/mcp/client.py:47` initialises `MCPClient` with inline default resolution.<br>`labs/mcp/client.py:74` normalises absent/invalid values to `"inline"`.<br>`labs/generator/external.py:101` reuses the shared inline descriptor cache when binding Azure payloads. |
| `gemini-placeholder-v0.3.6a` | Present | `labs/generator/external.py:1567` raises `NotImplementedError("Vertex AI structured-output unsupported")`.<br>`tests/test_external_generator.py:156` asserts that the placeholder exception text matches. |
| `azure-schema-binding-v0.3.6a` | Present | `labs/generator/external.py:2205` injects `response_format={"type": "json_schema", ... "strict": True}` with inline schema metadata.<br>`labs/generator/external.py:2216` records the inline `schema_resolution` in `_latest_schema_binding`.<br>`tests/test_external_generator.py:331` verifies the binding reports `"schema_resolution" == "inline"`. |
| `response-parse-v0.3.6a` | Present | `labs/generator/external.py:2104` enforces an assistant choice payload before parsing.<br>`labs/generator/external.py:2120` deserialises strictly with `json.loads`.<br>`tests/test_external_generator.py:400` covers valid/invalid payload parsing paths. |
| `validation-confirmation-v0.3.6a` | Present | `labs/cli.py:281` calls `mcp_client.confirm(asset, strict=strict_flag)` post-review.<br>`labs/mcp/client.py:212` enforces strict confirmation semantics.<br>`tests/test_labs_mcp_modes.py:78` confirms strict failures raise `MCPValidationError`. |
| `error-handling-retry-v0.3.6a` | Present | `labs/generator/external.py:436` bounds retries to `max_retries` attempts.<br>`labs/generator/external.py:551` halts on non-retryable errors.<br>`tests/test_external_generator.py:423` shows recovery after transient `429` responses. |
| `structured-logging-v0.3.6a` | Present | `labs/generator/external.py:421` seeds telemetry with inline schema metadata before each run.<br>`labs/generator/external.py:653` writes inline `schema_resolution` to JSONL logs.<br>`tests/test_external_generator.py:135` asserts logged entries carry the inline resolution. |

## Top gaps & fixes

- None — inline resolution is now the enforced default end-to-end.

## Recommendations

- Continue monitoring MCP registry drift; rerun the inline binding tests if the schema bundle revs beyond 0.7.3 (`tests/test_external_generator.py:331`, `tests/test_labs_mcp_modes.py:48`).
