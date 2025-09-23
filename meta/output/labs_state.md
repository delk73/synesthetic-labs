# Synesthetic Labs State (v0.1 Audit)

## Summary of repo state

The `synesthetic-labs` repository is in a well-defined state for v0.1. The core generator and critic agents are implemented, tested, and documented. The project uses a containerized environment for reproducible testing and execution, with a clear entry point via `test.sh`. The MCP integration is handled via a STDIO bridge, with a stub for local testing. Logging is structured and directed to `meta/output/labs/`. The documentation is mostly accurate, with some minor divergences.

## Top gaps & fixes (3-5 bullets)

*   **Divergence in canonical baseline**: The `ControlGenerator` and `MetaGenerator` implementations provide a slightly expanded set of controls and tags compared to the `docs/labs_spec.md`.
*   **Incomplete test for MCP failure**: The tests for MCP failure handling are present but could be more comprehensive by testing more failure modes of the MCP adapter.
*   **README mentions non-existent `.env.example`**: The `README.md` refers to an `.env.example` file which does not exist in the repository.

## Alignment with labs_spec.md

| Spec item                               | Status    | Evidence                                                                                             |
| --------------------------------------- | --------- | ---------------------------------------------------------------------------------------------------- |
| Generator agent                         | Present   | `labs/agents/generator.py`                                                                           |
| Critic agent                            | Present   | `labs/agents/critic.py`                                                                              |
| Assembler                               | Present   | `labs/generator/assembler.py`                                                                        |
| Labs CLI                                | Present   | `labs/cli.py`                                                                                        |
| MCP adapter                             | Present   | `labs/mcp_stdio.py`, `labs/mcp_stub.py`                                                                |
| Shader: CircleSDF                       | Present   | `labs/generator/shader.py`                                                                           |
| Tone: Tone.Synth                        | Present   | `labs/generator/tone.py`                                                                             |
| Haptic: Generic device                  | Present   | `labs/generator/haptic.py`                                                                           |
| Controls: basic mouse mapping           | Divergent | `labs/generator/control.py` includes mappings for `u_px` and `u_py`.                                 |
| Meta: `category=multimodal`, `tags=["circle","baseline"]` | Divergent | `labs/generator/meta.py` includes additional tags.                                                   |

## Generator implementation

| Component         | Status  | Evidence                                                                                                                     |
| ----------------- | ------- | ---------------------------------------------------------------------------------------------------------------------------- |
| ShaderGenerator   | Present | `labs/generator/shader.py`, `tests/test_generator_components.py`                                                               |
| ToneGenerator     | Present | `labs/generator/tone.py`, `tests/test_generator_components.py`                                                                 |
| HapticGenerator   | Present | `labs/generator/haptic.py`, `tests/test_generator_components.py`                                                               |
| ControlGenerator  | Present | `labs/generator/control.py`, `tests/test_generator_components.py`                                                              |
| MetaGenerator     | Present | `labs/generator/meta.py`, `tests/test_generator_components.py`                                                                 |

## Critic implementation

| Responsibility                  | Status  | Evidence                                                                                                                            |
| ------------------------------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Review assets                   | Present | `labs/agents/critic.py:CriticAgent.review`                                                                                          |
| Invoke MCP validation           | Present | `labs/agents/critic.py:CriticAgent.review` calls the validator.                                                                     |
| Log outcomes                    | Present | `labs/agents/critic.py:CriticAgent.review` calls `log_jsonl`.                                                                       |
| Handle MCP unavailability       | Present | `labs/agents/critic.py` and `labs/mcp_stdio.py` handle `MCPUnavailableError`.                                                       |
| Support strict vs relaxed mode  | Present | `labs/agents/critic.py:is_fail_fast_enabled` checks `LABS_FAIL_FAST` environment variable.                                          |

## Assembler / Wiring step

*   **Parameter index**: The `AssetAssembler` correctly collects `input_parameters` from all components into a `parameter_index` (`labs/generator/assembler.py:_collect_parameters`).
*   **Dangling reference pruning**: The assembler prunes control mappings that reference parameters not present in the `parameter_index` (`labs/generator/assembler.py:_prune_controls`).
*   **Provenance**: The assembler injects provenance information, including the agent name, version, and timestamp, into the generated asset (`labs/generator/assembler.py:generate`).

## MCP integration

*   **Validation calls**: The `CriticAgent` invokes the MCP validator via the `StdioMCPValidator` which sends a JSON payload over STDIO (`labs/mcp_stdio.py:StdioMCPValidator.validate`).
*   **Failure handling**: `MCPUnavailableError` is raised and handled when the MCP adapter cannot be launched or fails. The `CriticAgent` logs the failure and can proceed in relaxed mode.
*   **Strict vs relaxed mode**: The `LABS_FAIL_FAST` environment variable controls whether an MCP failure is a hard error or a warning.

## Test coverage

| Feature                       | Tested? | Evidence                                                                                                                                                           |
| ----------------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Generator outputs             | Yes     | `tests/test_generator_components.py`                                                                                                                               |
| Assembler wiring              | Yes     | `tests/test_generator_assembler.py`                                                                                                                                |
| Generator → Critic pipeline   | Yes     | `tests/test_pipeline.py`                                                                                                                                           |
| CLI                           | Yes     | `tests/test_pipeline.py`                                                                                                                                           |
| Determinism                   | Yes     | `tests/test_determinism.py`                                                                                                                                        |
| MCP failure handling          | Yes     | `tests/test_critic.py:test_critic_fails_when_stdio_validator_unavailable`, `tests/test_critic.py:test_critic_handles_stub_failure`                                   |
| Relaxed mode                  | Yes     | `tests/test_critic.py:test_relaxed_mode_skips_validation`, `tests/test_pipeline.py:test_cli_generate_relaxed_mode_skips_validation`                                  |
| Prompt experiment harness     | Yes     | `tests/test_prompt_experiment.py`                                                                                                                                  |

## Dependencies and runtime

| Package | Used in         | Required/Optional |
| ------- | --------------- | ----------------- |
| pytest  | `tests/*.py`    | Required for tests|

## Environment variables

*   `MCP_ADAPTER_CMD`: **Required**. Command to execute the MCP STDIO adapter. No default. When unreachable, behavior depends on `LABS_FAIL_FAST`.
*   `LABS_FAIL_FAST`: Optional. Default: `1` (strict). If `0`/`false`/`off`, validation failures are logged as warnings, and the process continues. Otherwise, they are hard errors.
*   `SYN_SCHEMAS_DIR`: Optional. Path to a directory containing schema files for the MCP adapter.
*   `LABS_EXPERIMENTS_DIR`: Optional. Default: `meta/output/labs/experiments`. Directory where validated assets are persisted.

## Logging

*   **Structured JSONL**: All logs are written in JSONL format using `labs/logging.py:log_jsonl`.
*   **Provenance fields**: Logs include provenance information such as agent name, version, and timestamps.
*   **Location under `meta/output/`**: Generator and critic logs are stored in `meta/output/labs/generator.jsonl` and `meta/output/labs/critic.jsonl` respectively.

## Documentation accuracy

*   `README.md` is mostly accurate but refers to a non-existent `.env.example` file.
*   `docs/labs_spec.md` is also mostly accurate but has a minor divergence with the implementation regarding the canonical baseline for controls and meta tags.

## Detected divergences

*   **Expanded Baseline**: The implemented `ControlGenerator` and `MetaGenerator` produce a richer baseline than specified in `docs/labs_spec.md`. The spec mentions only `shader.u_px` and `shader.u_py` mappings, but the implementation includes more. The meta tags are also expanded beyond `["circle", "baseline"]`.
*   **Missing `.env.example`**: The `README.md` mentions `.env.example` but the file is not in the repository.

## Recommendations

*   **Align on baseline**: Decide whether to adopt the expanded baseline and update `docs/labs_spec.md` or to prune the implementation to match the spec.
*   **Create `.env.example`**: Create the `.env.example` file and document the environment variables there, as mentioned in the `README.md`.
*   **Improve MCP failure tests**: Add more tests to cover different MCP adapter failure scenarios.