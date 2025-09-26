# Synesthetic Labs State (v0.3.2 Audit)

## Summary of repo state

The repository is in a good state and largely compliant with the v0.3.2 spec. The TCP-by-default transport, external generator integration, and hardening goals are mostly met. Key strengths include deterministic asset generation, a robust CLI, and comprehensive logging. The main gaps are around missing or incomplete test coverage for specific failure modes (socket transport, resolver fallbacks) and some documentation drift.

## Top gaps & fixes (3-5 bullets)

*   **Missing Test Coverage:** Critical components like the `resolve_mcp_endpoint` fallback logic and critic's socket failure handling are not covered by tests.
*   **Documentation Drift:** The README and other documents do not consistently reflect that TCP is the default transport.
*   **Unused Environment Variables:** Some environment variables mentioned in documentation are no longer used and should be removed.
*   **Incomplete `AGENTS.md`:** The `AGENTS.md` file is out of date and does not reflect the current state of the agents.

## Alignment with labs_spec.md

| Spec item                               | Status    | Evidence                                                                                                                            |
| --------------------------------------- | --------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| TCP is default transport                | Present   | `labs/mcp_stdio.py:129` (`resolve_mcp_endpoint` returns "tcp" when `MCP_ENDPOINT` is unset)                                           |
| Socket transport is optional            | Present   | `tests/test_socket.py` (tests are skipped if `LABS_SOCKET_TESTS` is not set)                                                          |
| MCP validation always invoked           | Present   | `labs/agents/critic.py:58` (validation is called in all modes, with `fail_fast` controlling behavior on failure)                      |
| Prune unused backend variables          | Missing   | `.example.env` still contains `SYN_SCHEMAS_DIR` which is not used.                                                                    |
| Document socket optionality             | Present   | `README.md` mentions `LABS_SOCKET_TESTS`.                                                                                           |
| Critic socket failure coverage          | Missing   | `tests/test_critic.py` does not have a test case for socket unavailability.                                                         |
| `resolve_mcp_endpoint` fallback tested  | Missing   | No unit test for `resolve_mcp_endpoint` in `tests/`.                                                                                |
| Maintainer docs reference resolver      | Missing   | `docs/labs_spec.md` does not reference `resolve_mcp_endpoint`.                                                                      |

## Generator implementation

| Component           | Status    | Evidence                                                                |
| ------------------- | --------- | ----------------------------------------------------------------------- |
| `AssetAssembler`    | Present   | `labs/generator/assembler.py`                                           |
| `ShaderGenerator`   | Present   | `labs/generator/shader.py`                                              |
| `ToneGenerator`     | Present   | `labs/generator/tone.py`                                                |
| `HapticGenerator`   | Present   | `labs/generator/haptic.py`                                              |
| `ControlGenerator`  | Present   | `labs/generator/control.py`                                             |
| `MetaGenerator`     | Present   | `labs/generator/meta.py`                                                |

## Critic implementation

| Responsibility                  | Status    | Evidence                                                                                             |
| ------------------------------- | --------- | ---------------------------------------------------------------------------------------------------- |
| Reviews assets                  | Present   | `labs/agents/critic.py:58`                                                                           |
| Invokes MCP validation          | Present   | `labs/agents/critic.py:91`                                                                           |
| Handles validation failures     | Present   | `labs/agents/critic.py:94`                                                                           |
| Logs reviews                    | Present   | `labs/agents/critic.py:168`                                                                          |
| Records rating stubs            | Present   | `labs/agents/critic.py:171`                                                                          |

## Assembler / Wiring step

*   **Parameter Index:** `AssetAssembler._collect_parameters` correctly collects parameters from shader, tone, and haptic sections (`labs/generator/assembler.py:118`).
*   **Dangling Reference Pruning:** `AssetAssembler._prune_controls` correctly prunes control mappings with no corresponding parameter (`labs/generator/assembler.py:127`).
*   **Provenance:** `AssetAssembler.generate` correctly injects provenance information into the generated asset (`labs/generator/assembler.py:78`).

## Patch lifecycle

*   **Preview:** `preview_patch` logs a preview of a patch (`labs/patches.py:26`).
*   **Apply:** `apply_patch` applies a patch and validates the result using the critic (`labs/patches.py:43`).
*   **Rate Stubs:** `rate_patch` logs a rating stub for a patch (`labs/patches.py:68`).
*   **Logging:** All patch lifecycle events are logged to `meta/output/labs/patches.jsonl`.

## MCP integration

*   **STDIO, TCP-default, socket-optional validation:** `build_validator_from_env` correctly resolves the transport based on environment variables, with TCP as the default (`labs/mcp_stdio.py:140`).
*   **Failure handling:** The critic correctly handles MCP unavailability and other errors, controlled by the `LABS_FAIL_FAST` environment variable (`labs/agents/critic.py:58`).
*   **Strict vs relaxed mode:** Both modes invoke MCP validation; relaxed mode downgrades failures to warnings (`labs/agents/critic.py:58`).
*   **1 MiB caps:** The transport layer enforces a 1 MiB payload size limit (`labs/transport.py:13`).
*   **Reason/detail logging:** The critic logs detailed reasons for validation failures (`labs/agents/critic.py:68`).
*   **Resolver fallback:** `resolve_mcp_endpoint` correctly falls back to TCP when `MCP_ENDPOINT` is unset or invalid (`labs/mcp_stdio.py:129`).

## External generator integration

*   **Gemini/OpenAI interface:** `ExternalGenerator` provides a pluggable interface for external generators (`labs/generator/external.py:25`).
*   **Provenance logging:** External generator runs are logged with detailed provenance information to `meta/output/labs/external.jsonl` (`labs/generator/external.py:195`).
*   **CLI flags:** The CLI supports `--engine` flag to select an external generator (`labs/cli.py:108`).
*   **Error handling:** `ExternalGenerator` includes retry/backoff logic and structured error logging (`labs/generator/external.py:75`).
*   **MCP-enforced validation:** All external outputs are validated via the critic and MCP (`labs/cli.py:152`).

## Test coverage

| Feature                          | Tested? | Evidence                                                                                             |
| -------------------------------- | ------- | ---------------------------------------------------------------------------------------------------- |
| TCP transport                    | Yes     | `tests/test_tcp.py`                                                                                  |
| Socket transport                 | Yes     | `tests/test_socket.py` (optional)                                                                    |
| STDIO transport                  | Yes     | `tests/test_critic.py`                                                                               |
| `resolve_mcp_endpoint` fallback  | No      | No specific test case found.                                                                         |
| Critic socket failure coverage   | No      | `tests/test_critic.py` does not test for socket unavailability.                                        |
| External generator (mock)        | Yes     | `tests/test_external_generator.py`                                                                   |
| Patch lifecycle                  | Yes     | `tests/test_patches.py`                                                                              |
| Deterministic generation         | Yes     | `tests/test_determinism.py`                                                                          |

## Dependencies and runtime

| Package | Used in   | Required/Optional |
| ------- | --------- | ----------------- |
| pytest  | `tests/`  | Required          |

## Environment variables

*   `MCP_ENDPOINT`: "tcp" (default), "stdio", or "socket".
*   `MCP_HOST`: "127.0.0.1" (default).
*   `MCP_PORT`: "8765" (default).
*   `MCP_ADAPTER_CMD`: Command to run for STDIO adapter.
*   `MCP_SOCKET_PATH`: Path to Unix socket for socket adapter.
*   `LABS_EXPERIMENTS_DIR`: `meta/output/labs/experiments` (default).
*   `LABS_FAIL_FAST`: "1" (default).
*   `LABS_EXTERNAL_LIVE`: "0" (default).
*   `GEMINI_MODEL`: "gemini-pro" (default).
*   `OPENAI_MODEL`: "gpt-4o-mini" (default).
*   `OPENAI_TEMPERATURE`: "0.4" (default).
*   `SYN_SCHEMAS_DIR`: Unused.

## Logging

*   **Structured JSONL:** All logs are written in JSONL format.
*   **Provenance fields:** All logs include detailed provenance information.
*   **Patch/rating/external fields:** Specific fields are included for patch, rating, and external generator events.
*   **Reason/detail on transport failures:** Failures include detailed reason and detail fields.
*   **Location under meta/output/:** All logs are written to subdirectories of `meta/output/labs/`.

## Documentation accuracy

*   **README vs. labs_spec.md:** The README and `labs_spec.md` are mostly aligned, but the README is more up-to-date regarding the TCP-by-default transport.
*   **TCP as default, socket optional:** The README clearly states that TCP is the default and socket is optional.
*   **Maintainer docs reference resolver:** `docs/labs_spec.md` does not reference `resolve_mcp_endpoint`.
*   **Env cleanup:** `.example.env` still contains the unused `SYN_SCHEMAS_DIR` variable.

## Detected divergences

*   The `AGENTS.md` file is outdated and does not reflect the current state of the agents.
*   Test coverage is missing for `resolve_mcp_endpoint` fallback and critic socket failure handling.
*   The `SYN_SCHEMAS_DIR` environment variable is documented but not used.

## Recommendations

*   Add unit tests for `resolve_mcp_endpoint` to cover all fallback scenarios.
*   Add a test case to `tests/test_critic.py` to cover socket unavailability.
*   Remove the `SYN_SCHEMAS_DIR` environment variable from `.example.env` and any other documentation.
*   Update `AGENTS.md` to reflect the current state of the agents.
*   Update `docs/labs_spec.md` to reference `resolve_mcp_endpoint`.