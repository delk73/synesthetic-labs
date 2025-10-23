# Synesthetic Labs State Report (v0.3.6a)

## Summary of repo state

- CLI bootstrap loads `.env`, defaults the schema/engine env vars to the `0.7.3` lock, and preserves the `--engine` override for ad-hoc runs (`labs/cli.py:18`, `labs/cli.py:24`, `labs/cli.py:165`).
- External generators reuse the cached MCP schema descriptor to bind Azure requests directly to 0.7.3 metadata before logging each run (`labs/generator/external.py:102`, `labs/generator/external.py:2195`, `labs/generator/external.py:629`).
- Test coverage exercises strict JSON parsing, schema-bound retries, and MCP interactions around the schema lock (`tests/test_external_generator.py:400`, `tests/test_external_generator.py:443`, `tests/test_labs_mcp_modes.py:39`).

## Alignment (Rule → Status → Evidence)

| Rule | Status | Evidence |
| --- | --- | --- |
| `env-preload-v0.3.6a` | Present | `labs/cli.py:18` loads `.env` via `load_dotenv`.<br>`labs/cli.py:24` sets defaults for `LABS_SCHEMA_VERSION`, `LABS_FAIL_FAST`, and `LABS_EXTERNAL_ENGINE`.<br>`labs/cli.py:165` wires the `--engine` CLI override so users can supersede env settings. |
| `mcp-schema-pull-v0.3.6a` | Present | `labs/generator/external.py:102` pulls the shared MCP schema descriptor.<br>`labs/mcp/client.py:133` caches fetched schema metadata for reuse.<br>`tests/test_labs_mcp_modes.py:39` asserts `fetch_schema(..., version="0.7.3")` returns the locked version. |
| `gemini-placeholder-v0.3.6a` | Present | `labs/generator/external.py:1577` raises `NotImplementedError("Vertex AI structured-output unsupported")`.<br>`tests/test_external_generator.py:159` verifies the placeholder exception text. |
| `azure-schema-binding-v0.3.6a` | Present | `labs/generator/external.py:2195` resolves the MCP descriptor before dispatch.<br>`labs/generator/external.py:2205` injects a `json_schema` response format with `strict` enabled.<br>`tests/test_external_generator.py:322` confirms the binding metadata is recorded. |
| `response-parse-v0.3.6a` | Present | `labs/generator/external.py:2104` requires an assistant choice payload.<br>`labs/generator/external.py:2122` parses completions strictly via `json.loads`.<br>`tests/test_external_generator.py:400` covers good/bad payload parsing paths. |
| `validation-confirmation-v0.3.6a` | Present | `labs/cli.py:281` calls `mcp_client.confirm(asset, strict=strict_flag)`.<br>`labs/mcp/client.py:215` enforces strict MCP confirmation failures.<br>`tests/test_labs_mcp_modes.py:70` exercises the strict failure path. |
| `error-handling-retry-v0.3.6a` | Present | `labs/generator/external.py:436` bounds retries to `max_retries` attempts.<br>`labs/generator/external.py:551` stops immediately on non-retryable errors.<br>`tests/test_external_generator.py:443` demonstrates retry/backoff recovery after 429s. |
| `structured-logging-v0.3.6a` | Present | `labs/logging.py:30` writes structured JSONL with schema metadata.<br>`labs/generator/external.py:629` records engine, schema id, version, and resolution for each run.<br>`tests/test_external_generator.py:129` asserts the log stream includes schema fields. |

## Top gaps & fixes

- Legacy MCP confirmation still strips enriched metadata for 0.7.3 assets, so persisted runs lose provenance unless the backend upgrades (`labs/mcp/client.py:349`, `labs/mcp/client.py:385`).
- Schema descriptor resolution depends on cached MCP responses; registry drift would require refreshing the local cache to keep the pinned 0.7.3 bundle accurate (`labs/generator/external.py:102`, `labs/generator/external.py:2195`).

## Recommendations

- Add an integration test around `MCPClient.validate` to ensure `_strip_legacy_metadata` removes every enriched field that 0.7.3 disallows (`labs/mcp/client.py:385`).
- Extend the CLI/operator docs with guidance on the 0.7.3 lock and upgrade steps once MCP exposes enriched schemas (`docs/labs_spec.md:24`, `docs/labs_spec.md:67`).
