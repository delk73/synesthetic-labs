# Synesthetic Labs State Report (v0.3.6a)

## Summary of Repo State

- **Environment surfaces**: CLI startup now defaults and warns on every Synesthetic env knob, including `LABS_EXTERNAL_ENGINE`, `LABS_EXTERNAL_LIVE`, and all Azure/Gemini credentials.
- **External integrations**: Gemini remains gated behind an explicit placeholder, while Azure chat completions deliver structured JSON with schema-bound payloads and deterministic parsing.
- **Normalization & provenance**: Legacy (`0.7.3`) assets drop provenance after deterministic backfilling, and enriched schemas still emit the full provenance envelope with endpoint/deployment metadata.
- **Observability**: External run logs now record deployment identifiers, timestamps, and schema binding, giving operators a complete trail across engines.

## Alignment (Rule → Status → Evidence)

| Rule | Status | Evidence |
| --- | --- | --- |
| `env-preload-v0.3.6a` | Present | `labs/cli.py:16-74` loads dotenv once and seeds defaults for `LABS_EXTERNAL_ENGINE`/`LABS_EXTERNAL_LIVE` before warning about missing keys.<br>`labs/cli.py:78-96` iterates engine-specific requirements, including `AZURE_OPENAI_API_VERSION` alongside Gemini credentials.<br>`requirements.txt:13` keeps `python-dotenv`, confirming the preload path. |
| `mcp-schema-pull-v0.3.6a` | Present | `labs/generator/external.py:24-133` caches `get_schema("synesthetic-asset", version=...)` results for downstream normalization.<br>`tests/test_mcp_schema_pull.py:12-44` asserts both `get_schema` and `list_schemas` return `ok` payloads. |
| `gemini-placeholder-v0.3.6a` | Present | `labs/generator/external.py:1493-1507` raises `NotImplementedError("Gemini structured-output is disabled until Vertex AI migration.")` on use.<br>`tests/test_external_generator.py:151-160` covers the placeholder with `pytest.raises`. |
| `azure-schema-binding-v0.3.6a` | Present | `labs/generator/external.py:1888-1967` builds chat-completion requests with `response_format={'type': 'json_object'}` and deployment-driven models.<br>`tests/test_external_generator.py:181-318` assert Azure payloads decode `message.content` JSON successfully. |
| `response-parse-v0.3.6a` | Present | `labs/generator/external.py:1742-1860` handles Gemini `candidates[0].content.parts` and OpenAI/Azure `choices[0].message.content` through `json.loads`.
`tests/test_external_generator.py:214-318` validate the deterministic parsing path. |
| `normalization-schema-0.7.3-v0.3.6a` | Present | `labs/generator/assembler.py:116-172` introduces `_fill_empty_sections` and strips meta provenance inside `_normalize_0_7_3`.<br>`tests/test_generator_assembler.py:12-53` confirm legacy assets retain `$schema`, filled scaffolds, and omit provenance. |
| `provenance-enriched-schema-v0.3.6a` | Present | `labs/generator/assembler.py:646-688` still injects engine, endpoint, deployment, api_version, and input parameters for ≥0.7.4.<br>`tests/test_generator.py:1-39` verify enriched assets surface generator provenance with trace IDs. |
| `cli-validation-flow-v0.3.6a` | Present | `labs/cli.py:223-282` invokes `invoke_mcp(...)`, persists relaxed runs, and records both critic/local MCP payloads.<br>`tests/test_pipeline.py:19-206` assert strict and relaxed flows across generate/critique commands. |
| `error-handling-retry-v0.3.6a` | Present | `labs/generator/external.py:322-520` retries 5xx/429 responses with capped backoff while failing fast on 4xx.<br>`tests/test_external_generator.py:320-370` cover rate-limit retries and authentication failures. |
| `structured-logging-v0.3.6a` | Present | `labs/generator/external.py:573-636` logs `deployment`, `endpoint`, schema binding, and validation metadata per run.<br>`tests/test_external_generator.py:181-249` and `tests/test_pipeline.py:260-318` assert deployment/timestamp fields in the external log stream. |
| `validation-passes-v0.3.6a` | Present | `labs/mcp/validate.py:141-189` enforces strict-mode failures via `invoke_mcp`, emitting relaxed warnings otherwise.<br>`tests/test_pipeline.py:82-206` capture both failure modes while still persisting relaxed assets. |
| `fallback-filling-v0.3.6a` | Present | `labs/generator/assembler.py:108-172` leverages `_fill_empty_sections` to backfill shader/tone/haptic/control defaults deterministically.<br>`tests/test_generator.py:40-88` and `tests/test_generator_assembler.py:12-53` verify filled sections across legacy assets. |

## Top Gaps & Fixes

1. **Env telemetry hardening**: Consider automated smoke tests that assert CLI warnings when flipping between Azure/Gemini engines and mock/live toggles.
2. **Schema regression guardrails**: Extend test coverage for mixed-schema pipelines (e.g., 0.7.3 assets flowing through CLI relaxed mode) to ensure provenance stays trimmed.
3. **External log tooling**: Add tooling to summarize the enriched external log stream (deployment/timestamp) for easier operator triage.

## Recommendations

- Add a targeted unit test for `_load_env_file` to assert warning coverage when `LABS_EXTERNAL_ENGINE` swaps to Gemini.
- Wire `_fill_empty_sections` into any future normalization helpers to keep legacy scaffolds deterministic.
- Build a lightweight analyzer that ships with ops docs to consume `meta/output/labs/external.jsonl` and flag missing deployment/timestamp fields.
