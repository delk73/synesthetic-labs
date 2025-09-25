# Synesthetic Labs State (v0.2-TCP)

## Summary of repo state
- Generator→critic pipeline ships v0.2 assets including modulation and rule bundle stubs with deterministic provenance (`labs/generator/assembler.py:62-113`, `labs/agents/generator.py:37-103`).
- STDIO, Unix socket, and TCP transports share framing, surface structured errors, and are covered by targeted tests (`labs/mcp_stdio.py:131-159`, `labs/mcp/socket_main.py:26-68`, `labs/mcp/tcp_client.py:17-46`, `tests/test_socket.py:29-88`, `tests/test_tcp.py:18-110`).
- Patch lifecycle commands log preview/apply/rate flows while the critic records rating stubs (`labs/patches.py:18-90`, `labs/cli.py:150-176`, `labs/agents/critic.py:137-159`).

## Top gaps & fixes (3-5 bullets)
- None pending for v0.2-TCP scope; continue monitoring MCP resiliency once integrated with non-stub adapters.
- Optional: document unused environment knobs (`SYN_EXAMPLES_DIR`, backend URLs) or wire them into transports for clarity (`.env:21-29`).
- Optional: extend critic error details beyond transport availability (e.g., schema failures) for richer telemetry (`labs/agents/critic.py:96-110`).

## Alignment with labs_spec.md (v0.2-TCP)
| Spec item | Status | Evidence |
| --- | --- | --- |
| STDIO MCP validation | Present | `labs/mcp_stdio.py:136-148`, `tests/test_pipeline.py:97-147` |
| Unix socket transport with size cap | Present | `labs/mcp_stdio.py:150-159`, `labs/transport.py:1-69`, `tests/test_socket.py:29-88` |
| TCP transport & CLI dispatch (`TcpMCPValidator`, `MCP_HOST`/`MCP_PORT`) | Present | `labs/mcp_stdio.py:131-159`, `labs/mcp/tcp_client.py:17-46`, `tests/test_tcp.py:18-110` |
| Patch lifecycle preview/apply/rate stubs | Present | `labs/patches.py:18-90`, `labs/cli.py:150-176`, `tests/test_patches.py:18-84` |
| Critic rating stub logging | Present | `labs/agents/critic.py:137-159`, `tests/test_ratings.py:6-21` |
| Modulation & rule bundle stubs attached to assets | Present | `labs/generator/assembler.py:62-88`, `tests/test_generator_assembler.py:18-40` |
| Path traversal guard | Present | `labs/core.py:9-28`, `tests/test_path_guard.py:8-32` |
| Non-root container execution | Present | `Dockerfile:1-12` |
| Docs cover STDIO + socket + TCP workflows | Present | `README.md:27-39`, `docs/labs_spec.md:109-142`

## Generator implementation
| Component | Status | Evidence |
| --- | --- | --- |
| AssetAssembler (parameter index + wiring) | Present | `labs/generator/assembler.py:56-113`, `tests/test_generator_assembler.py:18-40` |
| ShaderGenerator | Present | `labs/generator/shader.py:1-78` |
| ToneGenerator | Present | `labs/generator/tone.py:1-62` |
| HapticGenerator | Present | `labs/generator/haptic.py:1-52` |
| ControlGenerator | Present | `labs/generator/control.py:1-35` |
| MetaGenerator | Present | `labs/generator/meta.py:1-27` |
| Modulation stub integration | Present | `labs/generator/assembler.py:62-88`, `labs/experimental/modulation.py:1-53` |
| Rule bundle stub integration | Present | `labs/generator/assembler.py:62-88`, `labs/experimental/rule_bundle.py:1-49` |

## Critic implementation
| Responsibility | Status | Evidence |
| --- | --- | --- |
| Required field checks & issue reporting | Present | `labs/agents/critic.py:57-135`, `tests/test_critic.py:16-74` |
| MCP invocation & error handling | Present | `labs/agents/critic.py:68-135`, `tests/test_critic.py:65-118` |
| Fail-fast vs relaxed mode (`LABS_FAIL_FAST`) | Present | `labs/agents/critic.py:62-109`, `tests/test_pipeline.py:104-150` |
| Rating stub logging | Present | `labs/agents/critic.py:137-159`, `tests/test_ratings.py:6-21` |
| Structured TCP failure reason fields | Present | `labs/agents/critic.py:68-135`, `tests/test_tcp.py:58-90` |

## Assembler / Wiring step
- **Parameter index**: `_collect_parameters` gathers shader/tone/haptic parameters for control validation (`labs/generator/assembler.py:56-79`).
- **Dangling reference pruning**: `_prune_controls` discards mappings that target unknown parameters (`labs/generator/assembler.py:58-113`).
- **Provenance**: Assets embed assembler version, timestamp, and generator provenance (`labs/generator/assembler.py:62-72`, `labs/agents/generator.py:50-58`).

## Patch lifecycle
- **Preview**: Logs intended modifications without mutation (`labs/patches.py:18-34`).
- **Apply**: Applies updates, routes validation through the critic, and logs structured reviews (`labs/patches.py:37-65`, `tests/test_patches.py:35-63`).
- **Rate**: Delegates to critic rating stubs and records linkage (`labs/patches.py:68-90`, `tests/test_patches.py:65-84`).
- **Logging**: Lifecycle actions append to `meta/output/labs/patches.jsonl` via `log_jsonl` (`labs/patches.py:26-89`).

## MCP integration
- **STDIO validation**: Launches adapter command with env overrides and payload cap (`labs/mcp_stdio.py:136-148`).
- **Unix socket validation**: AF_UNIX client enforces 1 MiB framing and unlink semantics (`labs/mcp_stdio.py:150-159`, `labs/mcp/socket_main.py:26-68`).
- **TCP validation**: Host/port client uses shared framing and propagates transport errors (`labs/mcp_stdio.py:131-159`, `labs/mcp/tcp_client.py:17-46`).
- **Failure handling**: `MCPUnavailableError` surfaces adapter/connection issues with structured error payloads (`labs/agents/critic.py:68-135`, `tests/test_tcp.py:58-90`).
- **Strict vs relaxed mode**: `LABS_FAIL_FAST` toggles failure vs skip logging (`labs/agents/critic.py:62-109`, `tests/test_pipeline.py:104-150`).

## Test coverage
| Feature | Tested? | Evidence |
| --- | --- | --- |
| Generator components | Yes | `tests/test_generator_components.py:20-65` |
| Asset assembler wiring & determinism | Yes | `tests/test_generator_assembler.py:18-40`, `tests/test_determinism.py:8-27` |
| CLI generate/critique flow | Yes | `tests/test_pipeline.py:97-177` |
| Critic fail-fast / relaxed behavior | Yes | `tests/test_critic.py:65-118` |
| Patch lifecycle preview/apply/rate | Yes | `tests/test_patches.py:18-84` |
| Rating logging | Yes | `tests/test_ratings.py:6-21` |
| Socket transport round-trip & caps | Yes | `tests/test_socket.py:29-69` |
| TCP transport & oversize handling | Yes | `tests/test_tcp.py:18-110` |
| Prompt experiment batching | Yes | `tests/test_prompt_experiment.py:6-58` |

## Dependencies and runtime
| Package | Used in | Required/Optional |
| --- | --- | --- |
| pytest | `tests/` | Required for development/testing (`requirements.txt:1`) |
| Python stdlib (argparse, json, socket, subprocess, etc.) | Runtime across `labs/` modules | Required |

## Environment variables
- `MCP_ENDPOINT` (`stdio` default): selects transport branch; invalid values raise `MCPUnavailableError` (`labs/mcp_stdio.py:131-161`).
- `MCP_ADAPTER_CMD`: required for STDIO transport; missing command fails fast (`labs/mcp_stdio.py:136-148`, `tests/test_critic.py:85-95`).
- `MCP_SOCKET_PATH`: required for socket transport and normalized via path guard (`labs/mcp_stdio.py:150-159`, `labs/core.py:9-28`).
- `MCP_HOST` / `MCP_PORT`: required for TCP transport and validated before connecting (`labs/mcp_stdio.py:131-159`, `tests/test_tcp.py:82-110`).
- `LABS_FAIL_FAST`: controls strict vs relaxed review behavior (`labs/agents/critic.py:20-105`, `tests/test_pipeline.py:104-150`).
- `LABS_EXPERIMENTS_DIR`: directs persisted experiment artifacts (`labs/cli.py:38-143`).
- `SYN_SCHEMAS_DIR`: forwarded to STDIO adapter with traversal rejection (`labs/mcp_stdio.py:142-147`, `labs/core.py:9-28`).
- Additional optional variables (`SYN_EXAMPLES_DIR`, backend URLs) are presently unused placeholders (`.env:21-29`).

## Logging
- JSONL logging helper writes newline-delimited records and creates directories as needed (`labs/logging.py:13-24`).
- Generator, critic, and patch lifecycle logs emit provenance, validation, and rating metadata under `meta/output/labs/` (`labs/agents/generator.py:60-103`, `labs/agents/critic.py:118-159`, `labs/patches.py:26-89`).
- TCP/Socket errors capture structured reason/detail codes for downstream observability (`labs/agents/critic.py:68-135`, `tests/test_tcp.py:58-90`).

## Documentation accuracy
- README documents STDIO, socket, and TCP configuration along with lifecycle commands (`README.md:19-45`).
- `docs/labs_spec.md` describes the v0.2 baseline, TCP scope, and exit criteria reflected in implementation (`docs/labs_spec.md:70-142`).

## Detected divergences
- None; implementation matches the visible v0.2-TCP specification.

## Recommendations
- Document or integrate the optional schema/example/backend environment variables to avoid configuration drift (`.env:21-29`).
- Expand critic error detail taxonomy beyond transport connectivity for richer diagnostics (`labs/agents/critic.py:96-110`).
