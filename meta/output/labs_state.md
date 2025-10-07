# Synesthetic Labs Audit Report (v0.3.5)

## Summary of Repo State
- External integrations, schema branching, and MCP coordination remain intact, but environment bootstrapping still relies on handwritten helpers that predate the v0.3.5 dotenv mandate.
- Gemini request/response handling meets the new structured JSON requirements, and retry logic keeps 5xx attempts bounded while stopping immediately on 4xx failures.
- Logging and provenance metadata need another iteration to surface the richer taxonomy/input-parameter traces expected by the refreshed spec, and sample configuration files have not been brought forward.

## Alignment
| Rule | Status | Evidence |
| --- | --- | --- |
| **env-preload-v0.3.5** | Divergent | `labs/cli.py`: custom `_load_env_file()` parses `.env` without `dotenv.load_dotenv` and never touches `GEMINI_MODEL`/`GEMINI_API_KEY`/`LABS_FAIL_FAST` during startup.<br>`requirements.txt`: omits the required `python-dotenv` dependency entirely. |
| **gemini-request-structure-v0.3.5** | Present | `labs/generator/external.py` (`GeminiGenerator._build_request`): builds `contents → parts → text` and sets `generationConfig` with `responseMimeType='application/json'` plus temperature/max token overrides. |
| **gemini-response-parse-v0.3.5** | Present | `labs/generator/external.py` (`GeminiGenerator._parse_response`): reads `candidates[0].content.parts[0].text` and `json.loads` the payload; `tests/test_external_generator.py::test_gemini_generator_normalises_asset` exercises the flow. |
| **normalization-provenance-v0.3.5** | Divergent | `labs/generator/external.py` (`_normalise_asset`): assembles `$schema` and `provenance` but never records any `input_parameters` inside the provenance block.<br>`tests/test_generator.py`: asserts `$schema`/`provenance` exist yet does not cover the missing `input_parameters`, leaving the gap untested. |
| **error-handling-retry-v0.3.5** | Present | `labs/generator/external.py` (`_classify_http_error`): flags 500–599 as `retryable=True` while 4xx (`auth_error`, `bad_response`) stay non-retryable.<br>`tests/test_external_generator.py`: `test_rate_limited_retries` shows repeated attempts, and `test_no_retry_on_auth_error` halts immediately on a 4xx. |
| **structured-logging-v0.3.5** | Divergent | `labs/generator/external.py` (`record_run`): writes to `external.jsonl` with engine/endpoint/trace_id but omits any `taxonomy` field required by the spec.<br>`tests/test_external_generator.py::test_gemini_generator_normalises_asset`: captured log lacks taxonomy coverage, so the omission persists. |
| **mcp-validation-flow-v0.3.5** | Present | `labs/cli.py`: `generate`/`critique` call `_build_validator_optional()` and toggle `LABS_FAIL_FAST` via `--strict/--relaxed` before invoking `CriticAgent`.<br>`tests/test_pipeline.py::test_cli_generate_flags_precedence`: verifies CLI flags flip `LABS_FAIL_FAST` and still drive MCP checks. |
| **external-live-toggle-v0.3.5** | Divergent | Repository has no `.env.example`, so `LABS_EXTERNAL_LIVE` is undocumented for operators.<br>`labs/generator/external.py`: constructor inspects `LABS_EXTERNAL_LIVE` to enable/disable live calls, but the CLI only warns on missing keys and never guides users toward the toggle. |

## Top Gaps & Fixes
1. Replace the handcrafted env loader with `python-dotenv`, wire in GEMINI model/API defaults, and add the dependency to `requirements.txt`.
2. Extend normalization output so `asset['provenance']` (or its generator sub-block) lists the resolved `input_parameters`, then memorialize the behavior in generator/external tests.
3. Enrich external logging records with a `taxonomy` field and update tests to assert its presence, mirroring the new spec vocabulary.
4. Ship a `.env.example` (or update docs) that documents `LABS_EXTERNAL_LIVE` and aligns the CLI guidance with the toggle behavior.

## Recommendations
1. After adopting `python-dotenv`, centralize environment validation (API keys, models, fail-fast) in a shared helper so CLI commands stay consistent.
2. Introduce regression tests around provenance payloads to lock in input-parameter coverage for both deterministic and external generators.
3. Add a logging schema definition (JSON Schema or dataclass) to keep taxonomy and provenance fields from regressing in future releases.
