## Summary of repo state
- Generator pipeline assembles canonical shader/tone/haptic/control/meta/modulation/rule sections, stamps provenance, and logs experiments when reviews pass (`labs/generator/assembler.py:56`, `labs/agents/generator.py:70`, `tests/test_pipeline.py:93`).
- Critic validates required fields, wraps MCP responses with structured reason/detail metadata, and feeds patch/rating logs across CLI flows (`labs/agents/critic.py:58`, `labs/agents/critic.py:139`, `labs/patches.py:57`).
- MCP bridges cover STDIO, socket, and TCP transports with shared 1 MiB payload guards while CLI subcommands reuse the same wiring (`labs/mcp_stdio.py:134`, `labs/transport.py:8`, `labs/cli.py:101`).
- Gemini/OpenAI integrations normalise external assets, inject provenance, and log attempts plus validation outcomes for CLI runs (`labs/generator/external.py:168`, `tests/test_external_generator.py:16`, `tests/test_pipeline.py:211`).

## Top gaps & fixes (3-5 bullets)
- Enforce MCP calls in relaxed mode by making `_build_validator_optional` return a validator (wrapping warnings instead of `None`) and updating tests that currently expect `validation_status="skipped"` (`labs/cli.py:59`, `labs/agents/critic.py:100`, `tests/test_critic.py:153`).
- Default to TCP when `MCP_ENDPOINT` is unset/invalid, fall back to STDIO only when explicitly requested, and refresh docs/env samples to match (`labs/mcp_stdio.py:132`, `labs/cli.py:59`, `README.md:31`).
- Add structured `failure.reason`/`failure.detail` to `record_failure` outputs and assert them in external generator tests to meet logging requirements (`labs/generator/external.py:197`, `tests/test_external_generator.py:52`).
- Document the `LABS_SOCKET_TESTS` opt-in (or adjust defaults) so socket coverage being skipped in CI is intentional and discoverable (`README.md:31`, `tests/test_socket.py:12`).
- Prune or explicitly deprecate unused backend/env knobs such as `SYN_BACKEND_URL`/`SYN_EXAMPLES_DIR` to reduce drift (`.env:28`, `docker-compose.yml:7`).

## Alignment with labs_spec.md (table: Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| --- | --- | --- |
| Generator → critic pipeline persists validated assets | Present | `labs/cli.py:126`, `tests/test_pipeline.py:93` |
| External engines reuse MCP validation with provenance logging | Present | `labs/generator/external.py:168`, `tests/test_pipeline.py:211` |
| TCP transport is default when MCP_ENDPOINT unset/invalid | Divergent | `labs/mcp_stdio.py:132`, `.example.env:1` |
| Relaxed mode still invokes MCP (severity downgrade only) | Divergent | `labs/agents/critic.py:100`, `tests/test_pipeline.py:63` |
| Socket transport optionality documented for CI skips | Missing | `README.md:31`, `tests/test_socket.py:12` |
| Failure logs include reason/detail for external generator outages | Divergent | `labs/generator/external.py:197`, `tests/test_external_generator.py:52` |

## Generator implementation (table: Component → Status → Evidence)
| Component | Status | Evidence |
| --- | --- | --- |
| AssetAssembler composes canonical sections with provenance | Present | `labs/generator/assembler.py:56`, `tests/test_generator_assembler.py:18` |
| Parameter index build + dangling control pruning | Present | `labs/generator/assembler.py:104`, `labs/generator/assembler.py:118` |
| GeneratorAgent logging + experiment recording | Present | `labs/agents/generator.py:70`, `tests/test_generator.py:18` |

## Critic implementation (table: Responsibility → Status → Evidence)
| Responsibility | Status | Evidence |
| --- | --- | --- |
| Required field checks and issue tracking | Present | `labs/agents/critic.py:58`, `tests/test_critic.py:23` |
| MCP invocation with transport-specific errors | Present | `labs/agents/critic.py:104`, `tests/test_critic.py:53` |
| Relaxed mode validation still enforced | Divergent | `labs/agents/critic.py:100`, `tests/test_critic.py:153` |
| Rating stub logging for patches | Present | `labs/agents/critic.py:170`, `tests/test_patches.py:54` |

## Assembler / Wiring step (bullets: parameter index, dangling reference pruning, provenance)
- Parameter index aggregates shader/tone/haptic inputs for downstream wiring (`labs/generator/assembler.py:104`).
- `_prune_controls` drops mappings without parameter coverage to prevent dangling references (`labs/generator/assembler.py:118`).
- Provenance records assembler agent/version/timestamp/seed on each asset (`labs/generator/assembler.py:75`).

## Patch lifecycle (bullets: preview, apply, rate stubs, logging)
- `preview_patch` logs intent and captured changes without mutating assets (`labs/patches.py:26`, `tests/test_patches.py:11`).
- `apply_patch` merges updates, runs the critic (including patch_id metadata), and logs the review (`labs/patches.py:54`, `tests/test_patches.py:25`).
- `rate_patch` records critic ratings alongside patch logs for RLHF hooks (`labs/patches.py:82`, `tests/test_patches.py:54`).

## MCP integration (bullets: STDIO, TCP-default, socket-optional validation; failure handling; strict vs relaxed mode; 1 MiB caps; reason/detail logging)
- STDIO path requires `MCP_ADAPTER_CMD` and normalises schema paths before launching the adapter (`labs/mcp_stdio.py:134`, `labs/mcp_stdio.py:141`).
- TCP client enforces 1 MiB caps and wraps connection errors in `MCPUnavailableError` (`labs/transport.py:8`, `labs/mcp/tcp_client.py:27`, `tests/test_tcp.py:41`).
- Default transport still resolves to STDIO rather than spec-mandated TCP when `MCP_ENDPOINT` is unset (`labs/mcp_stdio.py:132`, `.example.env:1`).
- Socket validator works but tests are opt-in gated via `LABS_SOCKET_TESTS`, so optionality needs explicit documentation (`labs/mcp_stdio.py:148`, `tests/test_socket.py:12`).
- Fail-fast mode logs structured `validation_error` payloads, yet relaxed mode currently skips MCP invocation instead of downgrading severity (`labs/agents/critic.py:140`, `labs/agents/critic.py:100`).

## External generator integration (bullets: Gemini/OpenAI interface, provenance logging, CLI flags, error handling, MCP-enforced validation)
- Gemini/OpenAI subclasses supply engine-specific defaults (model, safety, temperature) and reuse provenance injection (`labs/generator/external.py:332`, `labs/generator/external.py:382`).
- CLI `generate --engine` routes external assets through critic review and persistence with logging to `external.jsonl` (`labs/cli.py:108`, `tests/test_pipeline.py:211`).
- Successful runs persist attempt traces, MCP results, and `failure` metadata when validation fails (`labs/generator/external.py:168`, `tests/test_external_generator.py:36`).
- `record_failure` captures attempts and error text but omits the required structured reason/detail fields (divergent) (`labs/generator/external.py:197`, `tests/test_external_generator.py:52`).

## Test coverage (table: Feature → Tested? → Evidence)
| Feature | Tested? | Evidence |
| --- | --- | --- |
| Generator components & assembler wiring | Yes | `tests/test_generator_components.py:53`, `tests/test_generator_assembler.py:18` |
| Critic fail-fast error handling | Yes | `tests/test_critic.py:53` |
| Relaxed mode MCP invocation | Partial (skips) | `tests/test_critic.py:153`, `tests/test_pipeline.py:63` |
| TCP transport round-trip & caps | Yes | `tests/test_tcp.py:41`, `tests/test_tcp.py:76` |
| Socket transport | Skipped by default | `tests/test_socket.py:12` |
| External generator provenance & failure logging | Yes | `tests/test_external_generator.py:16`, `tests/test_external_generator.py:52` |

## Dependencies and runtime (table: Package → Used in → Required/Optional)
| Package | Used in | Required/Optional |
| --- | --- | --- |
| pytest | Test suite execution (`pytest -q`) | Required (`requirements.txt:1`) |

## Environment variables (bullets: name, default, transport defaults, behavior when MCP/external API unreachable, deprecated knobs)
- `MCP_ENDPOINT` defaults to `stdio`, overriding the TCP-first requirement; invalid values raise instead of falling back (`labs/mcp_stdio.py:132`, `.example.env:1`).
- `MCP_ADAPTER_CMD`, `MCP_SOCKET_PATH`, `MCP_HOST`, and `MCP_PORT` select STDIO/socket/TCP transports respectively (`labs/mcp_stdio.py:135`, `labs/mcp_stdio.py:149`, `labs/mcp_stdio.py:160`).
- `LABS_FAIL_FAST` controls severity but currently causes relaxed mode to skip MCP entirely (`labs/agents/critic.py:21`, `labs/agents/critic.py:100`).
- `LABS_EXPERIMENTS_DIR` determines experiment persistence roots used by the CLI (`labs/cli.py:35`).
- External integrations honour `LABS_EXTERNAL_LIVE`, `GEMINI_MODEL`, `OPENAI_MODEL`, and `OPENAI_TEMPERATURE` for mock/live behaviour (`labs/generator/external.py:61`, `labs/generator/external.py:384`).
- `SYN_SCHEMAS_DIR` feeds schema lookup, while `SYN_EXAMPLES_DIR`/`SYN_BACKEND_URL` remain unused and should be deprecated or removed (`labs/mcp_stdio.py:141`, `.env:24`, `.env:28`).

## Logging (bullets: structured JSONL, provenance fields, patch/rating/external fields, reason/detail on transport failures, location under meta/output/)
- `log_jsonl` creates directories and appends sorted JSON lines under `meta/output/labs/` (`labs/logging.py:21`, `labs/generator/external.py:34`).
- Generator, critic, and patch modules log assets, reviews, and ratings with provenance and `validation_error` fields for MCP issues (`labs/agents/generator.py:70`, `labs/agents/critic.py:140`, `labs/patches.py:57`).
- External success logs include attempts, MCP results, and `failure.reason/detail` for validation failures, but transport outages emit only `status`/`error` (divergent) (`labs/generator/external.py:189`, `labs/generator/external.py:197`).

## Documentation accuracy (bullets: README vs. labs_spec.md; TCP as default, socket optional; env cleanup)
- README still advertises STDIO as the default transport and omits the TCP-first requirement from v0.3.1 (`README.md:31`).
- Documentation does not explain that socket validation is optional/disabled unless `LABS_SOCKET_TESTS` is set (`README.md:35`, `tests/test_socket.py:12`).
- Environment samples retain unused backend knobs contrary to the spec’s cleanup mandate (`.env:28`, `.example.env:1`).

## Detected divergences
- Relaxed mode skips MCP validation instead of downgrading severity (`labs/agents/critic.py:100`, `tests/test_pipeline.py:63`).
- Transport default remains STDIO and does not fall back to TCP when unset (`labs/mcp_stdio.py:132`, `.example.env:1`).
- External generator failure logs lack structured reason/detail fields (`labs/generator/external.py:197`).
- Socket optionality is undocumented despite tests being gated by `LABS_SOCKET_TESTS` (`README.md:35`, `tests/test_socket.py:12`).
- Unused backend/environment knobs persist (`.env:28`, `docker-compose.yml:7`).

## Recommendations
- Refactor `_build_validator_optional` and related tests so both strict and relaxed modes invoke MCP, logging warnings instead of marking validation `skipped` (`labs/cli.py:59`, `labs/agents/critic.py:100`, `tests/test_critic.py:153`).
- Update `build_validator_from_env` (and README/env samples) to treat TCP as the default transport fallback, with explicit selection for STDIO/socket (`labs/mcp_stdio.py:132`, `README.md:31`, `.example.env:1`).
- Extend `ExternalGenerator.record_failure` to emit `failure.reason/detail` alongside `status`/`error` and assert them in failure tests (`labs/generator/external.py:197`, `tests/test_external_generator.py:52`).
- Remove or clearly deprecate unused env variables (`SYN_BACKEND_URL`, `SYN_EXAMPLES_DIR`) across config and documentation to align with the spec cleanup (`.env:24`, `.env:28`, `docker-compose.yml:7`).
