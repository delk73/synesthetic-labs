# Synesthetic Labs Audit Report (v0.3.4)

## Summary of Repo State

This report summarizes the alignment of the `synesthetic-labs` repository with the requirements outlined in the `v0.3.4` specification. The audit covers schema targeting, validation modes, environment configuration, transport protocols, external generator integration, and logging.

## Alignment

| Rule | Status | Evidence |
| --- | --- | --- |
| **schema-branching** | Present | `labs/generator/assembler.py` contains `$schema` and `schema_version`. `tests/test_generator_assembler.py` includes tests for `0.7.3` and `0.7.4`. |
| **mcp-validation-modes** | Present | `labs/cli.py` includes logic for `mcp_response` and `ok`. `labs/agents/critic.py` handles `mcp_unavailable` and `strict` mode. `tests/test_pipeline.py` verifies `relaxed` mode behavior. |
| **env-preload** | Missing | `labs/cli.py` does not reference `dotenv` or `load`. `requirements.txt` is missing `python-dotenv`. |
| **tcp-default** | Present | `labs/mcp_stdio.py` resolves to `tcp` by `default`. `tests/test_tcp.py` confirms `tcp` is the `default` transport. |
| **gemini-structured-request** | Present | `labs/generator/external.py` constructs requests with `contents`, `parts`, `text`, and `generationConfig` including `responseMimeType`. |
| **gemini-structured-response-parse** | Present | `labs/generator/external.py` parses the response from `candidates[0].content.parts[0].text` using `json.loads`. `tests/test_external_generator.py` confirms this. |
| **external-limits-retry** | Present | `labs/generator/external.py` enforces size limits (`256 * 1024`, `1024 * 1024`) and includes `X-Goog-Api-Key` and `Authorization` headers. `tests/test_external_generator.py` verifies no-retry on `4xx` errors. |
| **logging-provenance** | Present | `labs/logging.py` defines logging to `external.jsonl`. `labs/generator/external.py` logs `schema_version`, `trace_id`, `reason`, and `detail`. |
| **normalization-contract** | Present | `labs/generator/external.py` handles `bad_response` and `out_of_range` errors. `tests/test_external_generator.py` includes tests for these cases. |
| **deprecated-knobs** | Divergent | `LABS_EXTERNAL_LIVE` is present in `.example.env` but absent from `README.md`. |

## Top Gaps & Fixes

1.  **`env-preload` is Missing**: The CLI does not preload environment variables from a `.env` file. This can be fixed by adding `python-dotenv` to `requirements.txt` and invoking `dotenv.load_dotenv()` in `labs/cli.py`.
2.  **`deprecated-knobs` is Divergent**: The `LABS_EXTERNAL_LIVE` knob is still present in `.example.env`, which contradicts the requirement for its removal or explicit deprecation.

## Recommendations

1.  Implement the `env-preload` functionality to align with the specification.
2.  Remove the `LABS_EXTERNAL_LIVE` entry from `.example.env` to resolve the divergence.