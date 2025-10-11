# Synesthetic Labs State Report (v0.3.6a)

## Summary of Repo State

- **Environment surfaces**: CLI boot-time checks now surface every required Azure/Gemini variable, warn on unset `LABS_EXTERNAL_ENGINE`/`LABS_EXTERNAL_LIVE`, and keep dotenv preload centralized.
- **External integrations**: Gemini generation stays disabled behind a guarded placeholder, while Azure chat completions continue delivering schema-bound JSON with deterministic parsing.
- **Normalization & provenance**: Legacy (`0.7.3`) assembly runs `_fill_empty_sections`, strips provenance, and keeps enriched schemas emitting full generator metadata.
- **Observability**: External run logs now capture deployment identifiers, timestamps, and schema binding so operators can correlate runs across environments.

## Alignment (Rule → Status → Evidence)

| Rule | Status | Evidence |
| --- | --- | --- |
| `env-preload-v0.3.6a` | Present | `labs/cli.py:16-74` loads `.env`, seeds defaults for `LABS_EXTERNAL_ENGINE`/`LABS_EXTERNAL_LIVE`, and centralizes warning emission.<br>`labs/cli.py:78-96` enumerates engine-specific keys, including `AZURE_OPENAI_API_VERSION` and Gemini credentials.<br>`requirements.txt:13` retains `python-dotenv`, validating the preload path. |
| `mcp-schema-pull-v0.3.6a` | Present | `labs/generator/external.py:24-133` caches schema lookups for `synesthetic-asset` versions.<br>`tests/test_mcp_schema_pull.py:12-44` ensures both `get_schema` and `list_schemas` succeed. |
| `gemini-placeholder-v0.3.6a` | Present | `labs/generator/external.py:1493-1507` raises `NotImplementedError` to keep Gemini structured output disabled.<br>`tests/test_external_generator.py:151-160` exercises the guard. |
| `azure-schema-binding-v0.3.6a` | Present | `labs/generator/external.py:1888-1967` builds Azure payloads with `response_format={'type': 'json_object'}` and deployment-scoped models.<br>`tests/test_external_generator.py:181-318` verify decoding of `message.content` JSON. |
| `response-parse-v0.3.6a` | Present | `labs/generator/external.py:1742-1860` normalizes Gemini parts and Azure/OpenAI messages with deterministic `json.loads`.
`tests/test_external_generator.py:214-318` cover both parsing branches. |
| `normalization-schema-0.7.3-v0.3.6a` | Present | `labs/generator/assembler.py:108-172` adds `_fill_empty_sections` and removes provenance inside `_normalize_0_7_3`.
`tests/test_generator_assembler.py:12-53` assert filled scaffolds with no provenance. |
| `provenance-enriched-schema-v0.3.6a` | Present | `labs/generator/assembler.py:646-688` continues injecting endpoint, deployment, and input parameter provenance for ≥0.7.4.
`tests/test_generator.py:1-39` validate generator metadata and trace IDs. |
| `cli-validation-flow-v0.3.6a` | Present | `labs/cli.py:223-282` routes assets through `invoke_mcp`, persisting relaxed runs and surfacing strict failures.
`tests/test_pipeline.py:19-206` cover both strict and relaxed CLI paths. |
| `error-handling-retry-v0.3.6a` | Present | `labs/generator/external.py:322-520` retries 5xx/429 responses with capped backoff.
`tests/test_external_generator.py:320-370` assert retry vs. fail-fast behaviour. |
| `structured-logging-v0.3.6a` | Present | `labs/generator/external.py:573-636` records deployment, endpoint, schema binding, and validation in each log record.
`tests/test_external_generator.py:181-249` and `tests/test_pipeline.py:260-318` assert deployment/timestamp fields. |
| `validation-passes-v0.3.6a` | Present | `labs/mcp/validate.py:141-189` enforces strict-mode failures with relaxed warnings.
`tests/test_pipeline.py:82-206` confirm persisted relaxed runs and strict aborts. |
| `fallback-filling-v0.3.6a` | Present | `labs/generator/assembler.py:108-172` uses `_fill_empty_sections` to keep shader/tone/haptic/control scaffolds deterministic.
`tests/test_generator.py:40-88` and `tests/test_generator_assembler.py:12-53` verify the helper across legacy assets. |

## Top Gaps & Fixes

1. **Env telemetry guardrails**: Add smoke tests that assert CLI warnings when toggling between Azure and Gemini engines.
2. **Legacy pipeline defense**: Keep monitoring mixed-schema flows (e.g., relaxed CLI runs) so trimmed provenance never leaks back into 0.7.3 assets.
3. **Log analytics tooling**: Provide an ops-facing summarizer over `meta/output/labs/external.jsonl` to surface deployment/timestamp data quickly.

## Recommendations

- Backstop `_load_env_file` with targeted unit coverage to prevent future regressions in warning scope.
- Reuse `_fill_empty_sections` for any new schema migration helpers to preserve deterministic defaults.
- Ship lightweight documentation or scripts showing how to parse the enriched external log stream for audits.
