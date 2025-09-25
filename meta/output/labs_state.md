## Summary of repo state
- CLI `generate` drives Generator → Critic → MCP validation before persisting experiments under `meta/output/labs/experiments/` (`labs/cli.py:108`, `tests/test_pipeline.py:93`).
- AssetAssembler produces canonical shader/tone/haptic/control/meta/modulation/rule sections with deterministic IDs and pruned controls (`labs/generator/assembler.py:44`, `tests/test_generator_assembler.py:21`).
- External generators normalize Gemini/OpenAI assets, inject provenance, and log MCP-reviewed attempts with structured failure metadata (`labs/generator/external.py:168`, `tests/test_external_generator.py:40`).
- Patch lifecycle stubs log preview/apply/rate operations alongside critic reviews and ratings (`labs/patches.py:26`, `tests/test_patches.py:25`).

## Top gaps & fixes (3-5 bullets)
- Add socket-transport coverage so critic failures assert `socket_unavailable` detail just like the new TCP/STDIO cases (`tests/test_critic.py:23`, `tests/test_critic.py:96`).
- Consider a focused unit test for `resolve_mcp_endpoint` to lock transport fallback behaviour when environment variables change (`labs/mcp_stdio.py:129`).
- Extend docs for maintainers to call out the new transport provenance hook so future agents reuse it consistently (`labs/mcp_stdio.py:129`, `labs/agents/critic.py:68`).

## Alignment with labs_spec.md (table: Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| --- | --- | --- |
| Generator → critic pipeline persists validated assets | Present | `labs/cli.py:108`, `tests/test_pipeline.py:93` |
| TCP transport is default when MCP_ENDPOINT unset/invalid | Present | `labs/mcp_stdio.py:140`, `tests/test_tcp.py:140` |
| Socket transport optional and documented | Present | `tests/test_socket.py:12`, `README.md:55` |
| Relaxed mode still attempts MCP validation (warnings only) | Present | `labs/agents/critic.py:46`, `tests/test_pipeline.py:152` |
| External generator failures emit reason/detail metadata | Present | `labs/generator/external.py:197`, `tests/test_external_generator.py:40` |
| Validation error detail identifies actual transport | Present | `labs/agents/critic.py:68`, `tests/test_critic.py:23` |

## Generator implementation (table: Component → Status → Evidence)
| Component | Status | Evidence |
| --- | --- | --- |
| Canonical section assembly & control pruning | Present | `labs/generator/assembler.py:44`, `tests/test_generator_assembler.py:21` |
| Deterministic identifiers when seeded | Present | `labs/generator/assembler.py:94`, `tests/test_determinism.py:10` |
| Experiment logging for validated runs | Present | `labs/agents/generator.py:64`, `tests/test_pipeline.py:137` |

## Critic implementation (table: Responsibility → Status → Evidence)
| Responsibility | Status | Evidence |
| --- | --- | --- |
| Required field checks and issue tracking | Present | `labs/agents/critic.py:58`, `tests/test_critic.py:23` |
| MCP invocation with structured error metadata | Present | `labs/agents/critic.py:88`, `tests/test_critic.py:71` |
| Relaxed mode downgrades severity while attempting MCP | Present | `labs/agents/critic.py:46`, `tests/test_critic.py:160` |
| Rating stub logging for patches | Present | `labs/agents/critic.py:171`, `tests/test_patches.py:54` |

## Assembler / Wiring step (bullets: parameter index, dangling reference pruning, provenance)
- Parameter index aggregates shader/tone/haptic inputs for downstream wiring (`labs/generator/assembler.py:104`).
- `_prune_controls` removes mappings without parameter coverage to avoid dangling references (`labs/generator/assembler.py:115`).
- Provenance stamps assembler agent/version/timestamp/seed onto each asset (`labs/generator/assembler.py:70`).

## Patch lifecycle (bullets: preview, apply, rate stubs, logging)
- `preview_patch` logs asset/patch IDs plus proposed updates without mutating the source asset (`labs/patches.py:26`, `tests/test_patches.py:11`).
- `apply_patch` merges updates, revalidates via Critic (including patch IDs), and logs the review payload (`labs/patches.py:37`, `tests/test_patches.py:25`).
- `rate_patch` records critic rating stubs alongside patch lifecycle entries for RLHF hooks (`labs/patches.py:68`, `tests/test_patches.py:54`).

## MCP integration (bullets: STDIO, TCP-default, socket-optional validation; failure handling; strict vs relaxed mode; 1 MiB caps; reason/detail logging)
- STDIO path requires `MCP_ADAPTER_CMD` and normalizes schema directories before launching the adapter (`labs/mcp_stdio.py:145`).
- TCP remains the default fallback, sharing the 1 MiB payload guard via `labs.transport` helpers (`labs/mcp_stdio.py:140`, `labs/transport.py:8`).
- Socket validation is optional and gated by `LABS_SOCKET_TESTS` to keep CI deterministic (`tests/test_socket.py:12`, `README.md:55`).
- `_build_validator_optional` keeps relaxed mode validating while downgrading outages to warnings (`labs/cli.py:59`, `labs/agents/critic.py:100`).
- `validation_error.detail` now echoes the resolved transport (`tcp_unavailable`, `stdio_unavailable`, etc.) thanks to `resolve_mcp_endpoint` (`labs/agents/critic.py:68`, `tests/test_critic.py:35`).

## External generator integration (bullets: Gemini/OpenAI interface, provenance logging, CLI flags, error handling, MCP-enforced validation)
- Gemini/OpenAI subclasses supply engine defaults and normalize assets with provenance including engine, mode, and trace ID (`labs/generator/external.py:93`, `labs/generator/external.py:332`).
- CLI `generate --engine` runs still flow through Critic/MCP and persist experiments on success (`labs/cli.py:113`, `tests/test_pipeline.py:200`).
- Successful runs append attempts, MCP responses, and validation status to `external.jsonl` (`labs/generator/external.py:168`, `tests/test_external_generator.py:18`).
- `record_failure` logs retry traces with structured `failure.reason/detail` when transports fail (`labs/generator/external.py:197`, `tests/test_external_generator.py:40`).

## Test coverage (table: Feature → Tested? → Evidence)
| Feature | Tested? | Evidence |
| --- | --- | --- |
| Generator assembler wiring & determinism | Yes | `tests/test_generator_assembler.py:21`, `tests/test_determinism.py:10` |
| Generator ↔ critic CLI pipeline & persistence | Yes | `tests/test_pipeline.py:93`, `tests/test_pipeline.py:117` |
| Critic fail-fast vs relaxed handling | Yes | `tests/test_critic.py:55`, `tests/test_critic.py:160` |
| External generator provenance & failure logging | Yes | `tests/test_external_generator.py:18`, `tests/test_external_generator.py:40` |
| TCP transport round-trip, caps, default fallback | Yes | `tests/test_tcp.py:41`, `tests/test_tcp.py:140` |
| Socket transport | Optional (gated) | `tests/test_socket.py:12`, `tests/test_socket.py:33` |
| Logging helper timestamp | Yes | `tests/test_logging.py:8` |

## Dependencies and runtime (table: Package → Used in → Required/Optional)
| Package | Used in | Required/Optional |
| --- | --- | --- |
| pytest | Test suite execution via `pytest -q` | Required (`requirements.txt:1`) |

## Environment variables (bullets: name, default, transport defaults, behavior when MCP/external API unreachable, deprecated knobs)
- `MCP_ENDPOINT` selects `tcp` (default via fallback), `stdio`, or `socket`; `resolve_mcp_endpoint` centralizes this logic (`labs/mcp_stdio.py:129`, `labs/mcp_stdio.py:140`).
- `MCP_HOST`/`MCP_PORT` configure TCP transport, while `MCP_ADAPTER_CMD` and `MCP_SOCKET_PATH` are required for STDIO/socket (`labs/mcp_stdio.py:145`, `labs/mcp_stdio.py:159`).
- `LABS_FAIL_FAST=1` enforces strict validation, while `0` keeps validating but downgrades outages to warnings (`labs/agents/critic.py:46`, `.env:19`).
- `LABS_EXPERIMENTS_DIR` controls asset persistence roots for CLI runs (`labs/cli.py:35`).
- External engines honor `LABS_EXTERNAL_LIVE`, `GEMINI_MODEL`, `OPENAI_MODEL`, and `OPENAI_TEMPERATURE` when building requests (`labs/generator/external.py:61`, `labs/generator/external.py:384`).
- `SYN_SCHEMAS_DIR` is forwarded to STDIO validators to locate schema bundles (`labs/mcp_stdio.py:151`).

## Logging (bullets: structured JSONL, provenance fields, patch/rating/external fields, reason/detail on transport failures, location under meta/output/)
- `log_jsonl` materializes directories and appends sorted JSON lines under `meta/output/labs/` (`labs/logging.py:13`).
- Generator logs capture assembled assets plus experiment validation summaries (`labs/agents/generator.py:60`, `tests/test_pipeline.py:137`).
- Critic reviews include `validation_status`, `validation_reason`, and transport-tagged `validation_error` metadata (`labs/agents/critic.py:68`, `tests/test_critic.py:35`).
- External runs log attempts, MCP results, and structured failure metadata for retry exhaustion (`labs/generator/external.py:168`, `tests/test_external_generator.py:40`).
- Patch lifecycle events and critic ratings append to JSONL streams for preview/apply/rate actions (`labs/patches.py:26`, `tests/test_patches.py:25`).

## Documentation accuracy (bullets: README vs. labs_spec.md; TCP as default, socket optional; env cleanup)
- README documents TCP as the default transport, optional socket tests, and relaxed-mode behaviour aligning with the spec (`README.md:31`, `README.md:55`).
- `.env` comment now explains that `LABS_FAIL_FAST=0` keeps validating while downgrading outages to warnings (`.env:19`).
- Docs and samples avoid unused backend knobs, focusing on the required MCP/env configuration (`README.md:31`, `.env:24`).

## Detected divergences
- None.

## Recommendations
- Add a critic regression test that sets `MCP_ENDPOINT=socket` and asserts `validation_error.detail == "socket_unavailable"` to mirror the new TCP/STDIO coverage (`tests/test_critic.py:23`, `tests/test_socket.py:33`).
- Introduce a small unit test for `resolve_mcp_endpoint` to freeze the fallback behaviour when unexpected endpoint strings appear (`labs/mcp_stdio.py:129`).
- Document the transport provenance helper in developer docs so future agents surface consistent `validation_error.detail` fields (`labs/mcp_stdio.py:129`, `labs/agents/critic.py:68`).
