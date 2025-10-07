# Synesthetic Labs Audit Report (v0.3.4)

## Summary of Repo State
- Codebase targets Synesthetic Labs spec v0.3.4 with schema-branching, MCP validation paths, transport fallbacks, and external generator integrations already implemented.
- Environment handling preloads `.env` files, merges into `os.environ`, and warns for missing API credentials before defaulting to mock external runs.
- Remaining divergence is the lingering `LABS_EXTERNAL_LIVE` knob across documentation and configuration samples.

## Alignment
| Rule | Status | Evidence |
| --- | --- | --- |
| **schema-branching** | Present | `labs/generator/assembler.py` switches between legacy (0.7.3) and enriched assets while injecting `$schema`; `tests/test_generator_assembler.py` exercises schema versions 0.7.3 and 0.7.4. |
| **mcp-validation-modes** | Present | `labs/agents/critic.py` records MCP availability for strict vs relaxed runs; `labs/cli.py` only persists when `review['mcp_response']['ok']` is true; `tests/test_pipeline.py` covers relaxed validation behavior. |
| **env-preload** | Present | `labs/cli.py` loads `.env`, merges into `os.environ`, and warns when `GEMINI_API_KEY`/`OPENAI_API_KEY` are absent, triggering mock external mode defaults. |
| **tcp-default** | Present | `labs/mcp_stdio.py` resolves invalid or missing endpoints to TCP transport and `tests/test_tcp.py` confirms TCP is the default path. |
| **gemini-structured-request** | Present | `labs/generator/external.py` builds Gemini payloads with `contents/parts/text` and sets `generationConfig.responseMimeType` to `application/json`. |
| **gemini-structured-response-parse** | Present | `labs/generator/external.py` parses `candidates[0].content.parts[0].text` via `json.loads`; `tests/test_external_generator.py` validates structured response handling. |
| **external-limits-retry** | Present | `labs/generator/external.py` enforces 256KiB/1MiB size caps, sets `X-Goog-Api-Key`/`Authorization` headers, and stops retries on 4xx errors as verified by `tests/test_external_generator.py`. |
| **logging-provenance** | Present | `labs/logging.py` writes to `external.jsonl`; `labs/generator/external.py` records `schema_version`, `trace_id`, and failure `reason`/`detail` for provenance. |
| **normalization-contract** | Present | `labs/generator/external.py` flags unknown keys as `bad_response` and numeric violations as `out_of_range`, with regression tests in `tests/test_external_generator.py`. |
| **deprecated-knobs** | Divergent | `LABS_EXTERNAL_LIVE` still appears in `.example.env`, runtime warnings, and docs rather than being removed or explicitly deprecated. |

## Top Gaps & Fixes
1. Deprecate or remove `LABS_EXTERNAL_LIVE` from `.example.env`, runtime warnings, and documentation to satisfy the knob retirement requirement.

## Recommendations
1. Update CLI warnings and docs to describe the mock-mode default without referencing `LABS_EXTERNAL_LIVE`.
2. Strip or clearly mark `LABS_EXTERNAL_LIVE` as deprecated in configuration samples and tests.
