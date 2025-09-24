# Synesthetic Labs State (v0.2 Audit)

## Summary of repo state

The repository is in good alignment with the v0.2 specification. The core deliverables—a generator/critic pipeline, STDIO and Unix socket MCP integration, and a preliminary patch lifecycle—are all present and functional. The codebase is clean, well-structured, and adheres to the prescribed deterministic and minimalist style. Tests provide good coverage for the implemented features.

## Top gaps & fixes

1.  **Minimal Dependencies**: The project intentionally uses only the Python standard library for its core logic, with `pytest` as the sole development dependency. This is not a gap but a significant design choice that should be explicitly documented as a project convention.
2.  **Container Test Command**: The `Dockerfile` defaults to running `pytest -q`. While this validates the code, a more comprehensive end-to-end test using the provided `test.sh` or `e2e.sh` scripts would provide a stronger guarantee of containerized functionality.
3.  **Experimental Code**: The `labs/experimental` module contains stubs for `ModulationGenerator` and `RuleBundleGenerator`. These are aligned with the v0.2 spec ("stubs") but should be clearly marked as non-functional placeholders in the documentation to avoid confusion.

## Alignment with labs_spec.md

| Spec item | Status | Evidence |
| :--- | :--- | :--- |
| Unix socket transport for MCP | Present | `labs/mcp/socket_main.py`, `labs/mcp_stdio.py:SocketMCPValidator`, `tests/test_socket.py` |
| Patch lifecycle (preview, apply, rate) | Present | `labs/patches.py`, `labs/cli.py`, `tests/test_patches.py` |
| Critic records ratings stub | Present | `labs/agents/critic.py:record_rating`, `tests/test_ratings.py` |
| Harden container (non-root user) | Present | `Dockerfile:3` (creates `labs` user), `Dockerfile:11` (sets `USER labs`) |
| Path traversal guard | Present | `labs/core.py:normalize_resource_path`, `tests/test_path_guard.py` |
| Docs align to STDIO/socket modes | Present | `README.md` accurately describes both `MCP_ENDPOINT` options. |
| Modulation & Rule bundle stubs | Present | `labs/experimental/modulation.py`, `labs/experimental/rule_bundle.py` |

## Generator implementation

| Component | Status | Evidence |
| :--- | :--- | :--- |
| AssetAssembler | Present | `labs/generator/assembler.py` |
| ShaderGenerator | Present | `labs/generator/shader.py` |
| ToneGenerator | Present | `labs/generator/tone.py` |
| HapticGenerator | Present | `labs/generator/haptic.py` |
| ControlGenerator | Present | `labs/generator/control.py` |
| MetaGenerator | Present | `labs/generator/meta.py` |
| Experimental Stubs | Present | `labs/experimental/` |

## Critic implementation

| Responsibility | Status | Evidence |
| :--- | :--- | :--- |
| Review asset for required keys | Present | `labs/agents/critic.py:review` |
| Coordinate MCP validation | Present | `labs/agents/critic.py` uses `build_validator_from_env` |
| Record rating stubs | Present | `labs/agents/critic.py:record_rating` |
| Fail-fast vs. relaxed mode | Present | `labs/agents/critic.py:is_fail_fast_enabled` |

## Assembler / Wiring step

*   **Parameter Index**: Present. `AssetAssembler._collect_parameters` builds a set of all available parameter names from the shader, tone, and haptic sections.
*   **Dangling Reference Pruning**: Present. `AssetAssembler._prune_controls` ensures that control mappings only target parameters that exist in the parameter index.
*   **Provenance**: Present. The `AssetAssembler` injects `provenance` data into the final asset, including agent name, version, and timestamp.

## Patch lifecycle

*   **Preview**: Present. `labs/patches.py:preview_patch` logs the intended patch without applying it. Exposed via `labs.cli preview`.
*   **Apply**: Present. `labs/patches.py:apply_patch` applies the patch and uses the `CriticAgent` to validate the result. Exposed via `labs.cli apply`.
*   **Rate**: Present. `labs/patches.py:rate_patch` uses the `CriticAgent` to log a rating stub. Exposed via `labs.cli rate`.
*   **Logging**: Present. All lifecycle events are logged to `meta/output/labs/patches.jsonl`.

## MCP integration

*   **STDIO and Socket Validation**: Present. `labs/mcp_stdio.py` provides `StdioMCPValidator` and `SocketMCPValidator`. The `build_validator_from_env` function switches between them based on the `MCP_ENDPOINT` environment variable.
*   **Failure Handling**: Present. `MCPUnavailableError` is raised on timeouts, connection errors, or non-zero exit codes from the adapter.
*   **Strict vs. Relaxed Mode**: Present. The `LABS_FAIL_FAST` environment variable controls whether an MCP failure is fatal or results in a skipped validation.

## Test coverage

| Feature | Tested? | Evidence |
| :--- | :--- | :--- |
| Generator (Unit) | Yes | `test_generator_components.py`, `test_generator_assembler.py` |
| Generator (E2E) | Yes | `test_generator_e2e.py` |
| Critic Agent | Yes | `test_critic.py` |
| Patch Lifecycle | Yes | `test_patches.py` |
| Socket Transport | Yes | `test_socket.py` |
| Path Traversal Guard | Yes | `test_path_guard.py` |
| Determinism | Yes | `test_determinism.py` |
| Ratings Logging | Yes | `test_ratings.py` |
| CLI Commands | Yes | `test_pipeline.py` |
| Container (non-root) | Yes | Verified in `Dockerfile`. |

## Dependencies and runtime

| Package | Used in | Required/Optional |
| :--- | :--- | :--- |
| pytest | `tests/` | Required (for development) |
| (Standard Library) | `labs/` | Required (runtime) |

## Environment variables

*   `MCP_ENDPOINT`: `stdio` (default) or `socket`. Controls the MCP transport mechanism.
*   `MCP_ADAPTER_CMD`: Command to execute the STDIO MCP adapter (e.g., `python -m labs.mcp_stub`).
*   `MCP_SOCKET_PATH`: Filesystem path to the Unix socket for the MCP adapter.
*   `SYN_SCHEMAS_DIR`: Optional path to a directory of schemas for the MCP adapter.
*   `LABS_EXPERIMENTS_DIR`: `meta/output/labs/experiments`. Directory for persisted assets.
*   `LABS_FAIL_FAST`: `1` (default). If `0` or `false`, MCP failures are non-fatal.

## Logging

*   **Structured JSONL**: All logs are written as newline-delimited JSON.
*   **Provenance Fields**: Generator and critic logs include agent, version, and timestamp fields for traceability.
*   **Patch/Rating Fields**: Patch and rating operations are logged with specific fields like `patch_id`, `asset_id`, and `rating`.
*   **Location**: All logs are written under `meta/output/labs/` as specified.

## Documentation accuracy

*   `README.md` is accurate and aligned with the v0.2 feature set, correctly describing the CLI, environment variables, and logging behavior for both STDIO and socket modes.
*   `docs/labs_spec.md` clearly outlines the scope for v0.1, v0.2, and beyond, providing a solid foundation for the audit.

## Detected divergences

No significant divergences from the v0.2 specification were detected. The implementation is a faithful execution of the documented scope. The minimalist dependency approach is a notable, but not divergent, design choice.

## Recommendations

1.  **Document Dependency Strategy**: Explicitly state in the `README.md` or a contributor guide that the core `labs` package intentionally avoids third-party dependencies.
2.  **Enhance Container Test**: Modify the `test.sh` or `e2e.sh` script to be the default command in the `Dockerfile` to provide a more robust end-to-end validation of the containerized environment.
3.  **Clarify Experimental Stubs**: Add comments or docstrings to the `labs/experimental` modules to clarify that they are non-functional stubs intended for future development.