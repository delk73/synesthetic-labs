## Summary of repo state
- Generator assembles canonical sections with provenance and logging handed through the CLI pipeline (`labs/generator/assembler.py:70`, `labs/agents/generator.py:48`, `labs/cli.py:149`).
- Critic enforces required keys, invokes MCP transports, and records structured validation outcomes (`labs/agents/critic.py:34`, `labs/agents/critic.py:104`, `labs/agents/critic.py:160`).
- Patch lifecycle stubs log preview/apply/rate operations alongside critic reviews and ratings (`labs/patches.py:26`, `labs/patches.py:57`, `labs/patches.py:82`).
- External Gemini/OpenAI generators share retry/backoff, provenance injection, and JSONL logging (`labs/generator/external.py:97`, `labs/generator/external.py:159`, `labs/generator/external.py:328`).

## Top gaps & fixes (3-5 bullets)
- Relaxed mode skips MCP validation entirely, violating the spec requirement to always call an adapter (`labs/cli.py:59`, `labs/agents/critic.py:100`).
- Unix socket tests remain gated behind an environment flag and default to skip, reducing coverage of the required transport (`tests/test_socket.py:12`).
- Sample environment still advertises unused backend variables, creating configuration drift (`.env:24`, `.env:28`).

## Alignment with labs_spec.md (table: Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| --- | --- | --- |
| ExternalGenerator interface with Gemini/OpenAI implementations | Present | `labs/generator/external.py:75`, `labs/generator/external.py:328`, `labs/generator/external.py:378` |
| CLI `generate --engine` routes through critic + MCP | Present | `labs/cli.py:77`, `labs/cli.py:126`, `labs/cli.py:136` |
| External runs logged under `meta/output/labs/external.jsonl` | Present | `labs/generator/external.py:159`, `labs/logging.py:30` |
| MCP transports (STDIO/socket/TCP) resolvable from env | Present | `labs/mcp_stdio.py:134`, `labs/mcp_stdio.py:148`, `labs/mcp_stdio.py:159` |
| Always call MCP validator even in relaxed mode | Divergent | `_build_validator_optional` returns `None` and critic marks validation `skipped` (`labs/cli.py:59`, `labs/agents/critic.py:100`) |
| Socket transport test coverage enabled by default | Divergent | Module skip when `LABS_SOCKET_TESTS` unset (`tests/test_socket.py:12`) |

## Generator implementation (table: Component → Status → Evidence)
| Component | Status | Evidence |
| --- | --- | --- |
| AssetAssembler composes shader/tone/haptic/control/meta/modulation/rule bundle | Present | `labs/generator/assembler.py:56`, `labs/generator/assembler.py:70` |
| Parameter index + control pruning | Present | `labs/generator/assembler.py:64`, `labs/generator/assembler.py:114` |
| GeneratorAgent stamps provenance and logs JSONL | Present | `labs/agents/generator.py:50`, `labs/agents/generator.py:60` |

## Critic implementation (table: Responsibility → Status → Evidence)
| Responsibility | Status | Evidence |
| --- | --- | --- |
| Required key verification and issue tracking | Present | `labs/agents/critic.py:34`, `labs/agents/critic.py:58` |
| MCP validator invocation with transport-specific errors | Present | `labs/agents/critic.py:104`, `labs/agents/critic.py:110` |
| Fail-fast toggle via `LABS_FAIL_FAST` | Present | `labs/agents/critic.py:21`, `labs/agents/critic.py:93` |
| Patch-aware review metadata | Present | `labs/agents/critic.py:157` |
| Rating stub logging | Present | `labs/agents/critic.py:170`, `labs/agents/critic.py:185` |

## Assembler / Wiring step (bullets: parameter index, dangling reference pruning, provenance)
- Parameter index aggregates shader/tone/haptic inputs before persistence (`labs/generator/assembler.py:104`).
- `_prune_controls` removes mappings without parameter coverage to avoid dangling references (`labs/generator/assembler.py:118`).
- Provenance records assembler agent, version, seed, and timestamp on each asset (`labs/generator/assembler.py:75`).

## Patch lifecycle (bullets: preview, apply, rate stubs, logging)
- `preview_patch` records intent without mutation and logs JSONL entries (`labs/patches.py:26`, `tests/test_patches.py:11`).
- `apply_patch` merges updates, invokes the critic, and logs validation results (`labs/patches.py:57`, `tests/test_patches.py:43`).
- `rate_patch` delegates to the critic’s rating logger and mirrors the payload in patch logs (`labs/patches.py:82`, `tests/test_patches.py:54`).

## MCP integration (bullets: STDIO, socket, TCP validation; failure handling; strict vs relaxed mode)
- STDIO validator requires `MCP_ADAPTER_CMD` and normalizes schema paths before launching the adapter (`labs/mcp_stdio.py:135`, `labs/mcp_stdio.py:143`).
- Socket validator enforces path normalization and 1 MiB framing via `SocketMCPValidator` (`labs/mcp_stdio.py:148`, `tests/test_socket.py:33`).
- TCP validator wraps connection errors and payload caps in `MCPUnavailableError` (`labs/mcp_stdio.py:159`, `labs/mcp/tcp_client.py:33`, `tests/test_tcp.py:66`).
- Fail-fast honored via `LABS_FAIL_FAST`, but relaxed mode allows validation skips (divergent) (`labs/agents/critic.py:93`, `labs/agents/critic.py:118`).

## External generator integration (bullets: Gemini/OpenAI interface, provenance logging, CLI flags, error handling)
- `ExternalGenerator.generate` retries requests, enriches context, and returns normalized assets (`labs/generator/external.py:97`, `labs/generator/external.py:115`).
- Provenance embeds engine, API version, parameters, and `trace_id` for downstream auditing (`labs/generator/external.py:296`, `labs/generator/external.py:303`).
- CLI flag `--engine` selects Gemini/OpenAI implementations and still routes through critic validation (`labs/cli.py:77`, `labs/cli.py:126`).
- Failures emit structured traces via `record_failure` and JSONL logging (`labs/generator/external.py:197`, `labs/logging.py:30`).

## Test coverage (table: Feature → Tested? → Evidence)
| Feature | Tested? | Evidence |
| --- | --- | --- |
| Generator→Critic pipeline | Yes | `tests/test_pipeline.py:12`, `tests/test_pipeline.py:93` |
| CLI `generate --engine` external flow | Yes | `tests/test_pipeline.py:191`, `tests/test_pipeline.py:211` |
| External generator normalization & logging | Yes | `tests/test_external_generator.py:16`, `tests/test_external_generator.py:36` |
| External failure handling | Yes | `tests/test_external_generator.py:52`, `tests/test_external_generator.py:69` |
| Logging helper timestamping | Yes | `tests/test_logging.py:10`, `tests/test_logging.py:16` |
| Patch lifecycle preview/apply/rate | Yes | `tests/test_patches.py:11`, `tests/test_patches.py:43`, `tests/test_patches.py:54` |
| TCP transport behaviors | Yes | `tests/test_tcp.py:66`, `tests/test_tcp.py:110` |
| Socket transport behaviors | Skipped by default | `tests/test_socket.py:12`, `tests/test_socket.py:33` |

## Dependencies and runtime (table: Package → Used in → Required/Optional)
| Package | Used in | Required/Optional |
| --- | --- | --- |
| pytest | Test suite runner (`pytest -q`) | Required (`requirements.txt:1`) |
| urllib.request (stdlib) | External live transport fallback | Required (`labs/generator/external.py:260`) |
| logging (stdlib) | Agents and CLI instrumentation | Required (`labs/cli.py:18`, `labs/generator/external.py:72`) |

## Environment variables (bullets: name, default, behavior when external API unavailable)
- `MCP_ENDPOINT` defaults to `stdio`; selects STDIO/socket/TCP validators with required companion vars (`labs/mcp_stdio.py:132`, `.env:7`).
- `MCP_ADAPTER_CMD`, `MCP_SOCKET_PATH`, `MCP_HOST`, `MCP_PORT` gate specific transports and raise `MCPUnavailableError` when missing (`labs/mcp_stdio.py:135`, `labs/mcp_stdio.py:150`, `labs/mcp_stdio.py:162`).
- `SYN_SCHEMAS_DIR` is normalized before being handed to STDIO adapters (`labs/mcp_stdio.py:143`, `.env:23`).
- `LABS_FAIL_FAST` toggles relaxed mode; when disabled the CLI skips validation entirely (divergent) (`labs/agents/critic.py:21`, `labs/cli.py:59`).
- `LABS_EXPERIMENTS_DIR` controls persistence root for validated assets (`labs/cli.py:34`, `labs/cli.py:130`).
- `LABS_EXTERNAL_LIVE` keeps external generators in mock mode unless explicitly enabled (`labs/generator/external.py:61`).
- `GEMINI_MODEL`, `OPENAI_MODEL`, `OPENAI_TEMPERATURE` tune engine parameters when live mode is active (`labs/generator/external.py:333`, `labs/generator/external.py:384`).
- When external APIs fail despite retries, `ExternalGenerationError` captures attempts and logs via `record_failure` (`labs/generator/external.py:156`, `labs/generator/external.py:197`).

## Logging (bullets: structured JSONL, provenance fields, patch/rating/external fields, location under meta/output/)
- `log_jsonl` ensures newline-delimited JSON and creates directories (`labs/logging.py:13`).
- Generator and critic streams reside under `meta/output/labs/` (`labs/agents/generator.py:60`, `labs/agents/critic.py:160`).
- Patch lifecycle events write to `meta/output/labs/patches.jsonl` with critic reviews and ratings (`labs/patches.py:64`, `labs/patches.py:89`).
- External runs append prompt, response, normalized asset, MCP result, and failures to `meta/output/labs/external.jsonl` (`labs/generator/external.py:159`, `labs/generator/external.py:197`).

## Documentation accuracy (bullets: README vs. labs_spec.md)
- README advertises v0.3 external engines, CLI flag, and logging location consistent with the spec (`README.md:3`, `README.md:67`).
- docs/labs_spec.md captures v0.3 scope, validation rules, logging, and testing expectations that align with implementation (`docs/labs_spec.md:120`, `docs/labs_spec.md:135`).
- README still lists unused backend env vars from legacy `.env`, mirroring configuration drift noted in gaps (`README.md:47`, `.env:28`).

## Detected divergences
- Relaxed mode bypasses MCP validation despite spec mandate for adapter calls (`labs/cli.py:59`, `labs/agents/critic.py:118`).
- Socket transport tests require an opt-in flag and skip under default settings, limiting assurance (`tests/test_socket.py:12`).
- Legacy backend env configuration remains documented without runtime usage (`.env:24`, `README.md:47`).

## Recommendations
- Enforce MCP validation even in relaxed mode by surfacing failures when no validator is available, matching the spec’s mandatory adapter requirement (`labs/cli.py:59`, `labs/agents/critic.py:118`).
- Enable Unix socket tests by default or feature-detect support so the mandated transport remains covered in CI (`tests/test_socket.py:12`).
- Prune unused backend environment variables from docs and samples to reduce configuration drift (`.env:24`, `README.md:47`).
