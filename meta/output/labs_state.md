# Synesthetic Labs State (v0.2-TCP Audit)

## Summary of repo state
- Generator→critic pipeline, patch lifecycle CLI, and JSONL logging match the prior v0.2 scope (`labs/agents/generator.py:15-104`, `labs/patches.py:18-90`).
- MCP validation only supports STDIO and Unix sockets; TCP transport required by v0.2-TCP is absent (`labs/mcp_stdio.py:131-161`, `labs/mcp/__main__.py:12-16`).
- Generator assets remain versioned `v0.1` and omit the modulation/rule bundle stubs called out in the v0.2 baseline (`labs/generator/assembler.py:24-80`, `tests/test_generator_assembler.py:32-38`).

## Top gaps & fixes (3-5 bullets)
- Implement `TcpMCPValidator` plus `MCP_HOST`/`MCP_PORT` routing in `build_validator_from_env` and CLI dispatch so `MCP_ENDPOINT=tcp` works (`labs/mcp_stdio.py:131-161`, `labs/mcp/__main__.py:12-16`).
- Update README/CLI docs once TCP exists; until then, remove or clearly flag unsupported TCP settings in `.env` (`README.md:27-38`, `.env:5-12`).
- Extend `AssetAssembler` and related tests to attach `modulation` and `rule_bundle` sections per spec (`labs/generator/assembler.py:62-79`, `tests/test_generator_assembler.py:32-38`).
- When adding TCP, emit structured failure reasons (`reason/detail`) in critic logs to match spec language (`labs/agents/critic.py:88-135`).

## Alignment with labs_spec.md (v0.2-TCP)
| Spec item | Status | Evidence |
| --- | --- | --- |
| STDIO MCP validation | Present | `labs/mcp_stdio.py:26-93`, `tests/test_pipeline.py:101-147` |
| Unix socket transport with size cap | Present | `labs/mcp_stdio.py:96-128`, `tests/test_socket.py:29-88` |
| TCP transport & CLI dispatch (`TcpMCPValidator`, `MCP_HOST`/`MCP_PORT`) | Missing | `labs/mcp_stdio.py:131-161`, `labs/mcp/__main__.py:12-16`, `docs/labs_spec.md:109-142` |
| Patch lifecycle preview/apply/rate stubs | Present | `labs/patches.py:18-90`, `labs/cli.py:150-176` |
| Critic rating stub logging | Present | `labs/agents/critic.py:137-159`, `tests/test_ratings.py:6-21` |
| Modulation & rule bundle stubs attached to assets | Missing | `labs/generator/assembler.py:62-79`, `tests/test_generator_assembler.py:32-38`, `docs/labs_spec.md:80-81` |
| Path traversal guard | Present | `labs/core.py:9-28`, `tests/test_path_guard.py:8-32` |
| Non-root container execution | Present | `Dockerfile:1-12` |
| Docs cover STDIO + socket + TCP workflows | Divergent | `README.md:27-38`, `.env:5-12`, `docs/labs_spec.md:109-142` |

## Generator implementation
| Component | Status | Evidence |
| --- | --- | --- |
| AssetAssembler (parameter index + wiring) | Present | `labs/generator/assembler.py:18-113`, `tests/test_generator_assembler.py:18-38` |
| ShaderGenerator | Present | `labs/generator/shader.py:1-78` |
| ToneGenerator | Present | `labs/generator/tone.py:1-62` |
| HapticGenerator | Present | `labs/generator/haptic.py:1-52` |
| ControlGenerator | Present | `labs/generator/control.py:1-35` |
| MetaGenerator | Present | `labs/generator/meta.py:1-27` |
| Modulation stub integration | Missing | `labs/generator/assembler.py:62-79`, `tests/test_generator_assembler.py:32-38` |
| Rule bundle stub integration | Missing | `labs/generator/assembler.py:62-79`, `tests/test_generator_assembler.py:32-38` |

## Critic implementation
| Responsibility | Status | Evidence |
| --- | --- | --- |
| Required field checks & issue reporting | Present | `labs/agents/critic.py:57-121`, `tests/test_critic.py:25-64` |
| MCP invocation & error handling | Present | `labs/agents/critic.py:68-110`, `tests/test_critic.py:65-118` |
| Fail-fast vs relaxed mode (`LABS_FAIL_FAST`) | Present | `labs/agents/critic.py:20-99`, `tests/test_critic.py:96-118` |
| Rating stub logging | Present | `labs/agents/critic.py:137-159`, `tests/test_ratings.py:6-21` |
| Structured TCP failure reason fields | Missing | `labs/agents/critic.py:118-135`, `docs/labs_spec.md:123-141` |

## Assembler / Wiring step
- **Parameter index**: Present via `_collect_parameters` storing shader/tone/haptic parameters (`labs/generator/assembler.py:56-79`).
- **Dangling reference pruning**: Present; `_prune_controls` drops mappings not in the parameter index (`labs/generator/assembler.py:58-113`).
- **Provenance**: Present; `provenance` embeds agent, version `v0.1`, timestamp, and seed (`labs/generator/assembler.py:62-72`).

## Patch lifecycle
- **Preview**: Logs intent without mutation (`labs/patches.py:18-34`).
- **Apply**: Applies updates then re-validates via critic (`labs/patches.py:37-65`).
- **Rate**: Delegates rating stub to critic and records it (`labs/patches.py:68-90`).
- **Logging**: All actions append JSONL records under `meta/output/labs/patches.jsonl` (`labs/patches.py:26-89`).

## MCP integration
- **STDIO validation**: `StdioMCPValidator` shells out to configured adapter and enforces payload caps (`labs/mcp_stdio.py:26-93`).
- **Unix socket validation**: `SocketMCPValidator` handles AF_UNIX connections with size checks (`labs/mcp_stdio.py:96-128`, `tests/test_socket.py:29-88`).
- **TCP validation**: Missing; `build_validator_from_env` rejects `MCP_ENDPOINT=tcp` and no TCP validator exists (`labs/mcp_stdio.py:131-161`).
- **Failure handling**: `MCPUnavailableError` raised on timeouts, exits, or socket errors (`labs/mcp_stdio.py:52-127`).
- **Strict vs relaxed mode**: `LABS_FAIL_FAST` toggles skip vs failure (`labs/agents/critic.py:62-109`, `tests/test_pipeline.py:104-134`).

## Test coverage
| Feature | Tested? | Evidence |
| --- | --- | --- |
| Generator components | Yes | `tests/test_generator_components.py:20-65` |
| Asset assembler wiring & determinism | Yes | `tests/test_generator_assembler.py:18-38`, `tests/test_determinism.py:8-27` |
| CLI generate/critique flow | Yes | `tests/test_pipeline.py:97-177` |
| Critic fail-fast / relaxed behavior | Yes | `tests/test_critic.py:65-118` |
| Patch lifecycle preview/apply/rate | Yes | `tests/test_patches.py:18-84` |
| Rating logging | Yes | `tests/test_ratings.py:6-21` |
| Socket transport round-trip & caps | Yes | `tests/test_socket.py:29-69` |
| Prompt experiment batching | Yes | `tests/test_prompt_experiment.py:6-58` |
| TCP transport & oversize handling | Missing | `labs/mcp_stdio.py:131-161` (no TCP validator), `tests/` lacks TCP cases (`rg "Tcp" tests` returns none) |

## Dependencies and runtime
| Package | Used in | Required/Optional |
| --- | --- | --- |
| pytest | Test suite (`tests/`) | Required for development/testing (`requirements.txt:1`) |
| Python stdlib (argparse, json, socket, etc.) | Runtime across `labs/` modules | Required |

## Environment variables
- `MCP_ENDPOINT` (default `stdio`): selects transport; unsupported values raise `MCPUnavailableError` (`labs/mcp_stdio.py:134-161`). When MCP is unreachable in strict mode the critic fails validation (`labs/agents/critic.py:62-99`).
- `MCP_ADAPTER_CMD` (no default): required for STDIO; absence causes immediate failure (`labs/mcp_stdio.py:136-147`, `tests/test_critic.py:85-95`).
- `MCP_SOCKET_PATH` (socket mode): normalized and required when `MCP_ENDPOINT=socket` (`labs/mcp_stdio.py:150-159`).
- `MCP_HOST` / `MCP_PORT`: documented in `.env` but unused—TCP transport not implemented (`.env:5-12`, `labs/mcp_stdio.py:131-161`).
- `LABS_FAIL_FAST` (default enabled): controls whether MCP outages fail or skip (`labs/agents/critic.py:20-99`, `tests/test_pipeline.py:104-150`).
- `LABS_EXPERIMENTS_DIR` (default `meta/output/labs/experiments`): directs persisted assets (`labs/cli.py:38-116`).
- `SYN_SCHEMAS_DIR` (optional): forwarded to STDIO adapter after path normalization (`labs/mcp_stdio.py:142-147`).
- `SYN_EXAMPLES_DIR`, `SYN_BACKEND_URL`, `SYN_BACKEND_ASSETS_PATH`: surfaced in `.env` but unused in code (potential cleanup) (`.env:21-29`).

## Logging
- Structured JSONL writer ensures newline-delimited records and directory creation (`labs/logging.py:13-24`).
- Generator logs asset payloads and experiment metadata to `meta/output/labs/generator.jsonl` (`labs/agents/generator.py:12-104`).
- Critic logs reviews and rating stubs to `meta/output/labs/critic.jsonl` (`labs/agents/critic.py:118-159`).
- Patch lifecycle appends preview/apply/rate records to `meta/output/labs/patches.jsonl` (`labs/patches.py:18-90`).

## Documentation accuracy
- README documents STDIO and socket transports but omits TCP despite spec requiring it (`README.md:27-38`, `docs/labs_spec.md:109-142`).
- `.env` advertises `MCP_ENDPOINT=tcp` with host/port variables that the code ignores (`.env:5-12`, `labs/mcp_stdio.py:131-161`).
- README explicitly states modulation and rule bundle generators are out of scope, contradicting v0.2 baseline that should include stubs (`README.md:57-59`, `docs/labs_spec.md:80-81`).

## Detected divergences
- TCP transport and associated logging/test coverage are missing even though v0.2-TCP requires them (`docs/labs_spec.md:109-142`, `labs/mcp_stdio.py:131-161`).
- Assets still omit modulation and rule bundle sections contrary to the v0.2 canonical baseline (`docs/labs_spec.md:80-81`, `tests/test_generator_assembler.py:32-38`).
- Documentation advertises unsupported TCP settings, risking misconfiguration (`.env:5-12`, `README.md:27-38`).

## Recommendations
- Add a `TcpMCPValidator` plus environment wiring and tests to cover round-trip, oversize payloads, and failure cases (`labs/mcp_stdio.py:131-161`, `tests/`).
- Update CLI launcher and documentation once TCP is implemented; until then, either support or clearly mark the `.env` TCP configuration as unavailable (`labs/mcp/__main__.py:12-16`, `.env:5-12`, `README.md:27-38`).
- Extend `AssetAssembler` and generator tests to include modulation and rule bundle stubs per spec (`labs/generator/assembler.py:62-79`, `docs/labs_spec.md:80-81`).
- Introduce structured failure payloads (e.g., `reason/detail`) when MCP validation is skipped or unavailable to satisfy logging expectations for TCP errors (`labs/agents/critic.py:118-135`, `docs/labs_spec.md:133-141`).
