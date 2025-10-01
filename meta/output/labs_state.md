# Synesthetic Labs State (v0.3.3 Audit)

## Summary of repo state
- Generator CLI and agent pipeline persists validated assets and records experiments via JSONL traces (labs/cli.py:108; labs/agents/generator.py:37; tests/test_pipeline.py:93)
- Critic enforces required fields, strict/relaxed MCP validation, and writes reason/detail fields to logs (labs/agents/critic.py:46; labs/agents/critic.py:70; tests/test_critic.py:55)
- MCP transports default to TCP with STDIO/socket options, shared 1 MiB caps, and resolver fallback coverage (labs/mcp_stdio.py:129; labs/transport.py:8; tests/test_tcp.py:163)
- Deprecated SYN_SCHEMAS_DIR remains auto-forwarded without the mandated warning and .env still endorses it, diverging from spec cleanup (docs/labs_spec.md:175; labs/mcp_stdio.py:152; .env:23)

## Top gaps & fixes (3-5 bullets)
- Emit a single deprecation warning when SYN_SCHEMAS_DIR is forwarded to STDIO so the runtime matches the spec’s cleanup requirement (docs/labs_spec.md:175; labs/mcp_stdio.py:152)
- Mark SYN_SCHEMAS_DIR as deprecated/STDIO-only in the committed .env sample to align with the documented policy (docs/labs_spec.md:174; .env:23)
- Extend maintainer-facing docs with an explicit reference to resolve_mcp_endpoint so transport provenance guidance stays discoverable (docs/labs_spec.md:164; docs/process.md:1)

## Alignment with labs_spec.md
| Spec item | Status | Evidence |
| --- | --- | --- |
| TCP default transport | Present | labs/mcp_stdio.py:129; tests/test_tcp.py:163 |
| STDIO/TCP/socket validators from env | Present | labs/mcp_stdio.py:145; labs/mcp_stdio.py:159; labs/mcp_stdio.py:170 |
| Strict and relaxed modes invoke MCP | Present | labs/agents/critic.py:63; tests/test_pipeline.py:63 |
| Failure logs include reason/detail | Present | labs/agents/critic.py:70; tests/test_critic.py:55 |
| 1 MiB payload caps enforced | Present | labs/transport.py:8; tests/test_tcp.py:110 |
| External generator provenance + MCP result logged | Present | labs/generator/external.py:115; tests/test_pipeline.py:211 |
| Socket optional with failure coverage | Present | tests/test_socket.py:9; tests/test_critic.py:186 |
| resolve_mcp_endpoint fallback tested | Present | tests/test_tcp.py:163; tests/test_tcp.py:171 |
| Env templates mark SYN_SCHEMAS_DIR deprecated STDIO-only | Divergent | docs/labs_spec.md:174; .env:23 |
| SYN_SCHEMAS_DIR warning logged on STDIO forwarding | Missing | docs/labs_spec.md:175; labs/mcp_stdio.py:152 |
| Maintainer docs reference resolver fallback | Missing | docs/labs_spec.md:164; docs/process.md:1 |

## Generator implementation
| Component | Status | Evidence |
| --- | --- | --- |
| GeneratorAgent JSONL tracing | Present | labs/agents/generator.py:37; labs/agents/generator.py:98 |
| AssetAssembler deterministic wiring | Present | labs/generator/assembler.py:44; tests/test_generator_assembler.py:21 |
| Component generators (shader/tone/haptic/control/meta) | Present | labs/generator/assembler.py:36; labs/generator/shader.py:87; labs/generator/tone.py:58; labs/generator/haptic.py:38; labs/generator/control.py:35; labs/generator/meta.py:14 |
| Modulation and rule bundle assemblers | Present | labs/generator/assembler.py:41; labs/experimental/modulation.py:45; labs/experimental/rule_bundle.py:52 |
| Experiment logging after validation | Present | labs/agents/generator.py:64; tests/test_pipeline.py:120 |

## Critic implementation
| Responsibility | Status | Evidence |
| --- | --- | --- |
| Required field checks + issue list | Present | labs/agents/critic.py:58; tests/test_critic.py:23 |
| Strict vs relaxed MCP handling | Present | labs/agents/critic.py:63; tests/test_pipeline.py:63; tests/test_pipeline.py:154 |
| Transport-specific reason/detail payloads | Present | labs/agents/critic.py:70; tests/test_critic.py:55 |
| Review JSONL logging | Present | labs/agents/critic.py:148; labs/logging.py:13 |
| Rating stub logging | Present | labs/agents/critic.py:170; tests/test_ratings.py:6 |

## Assembler / Wiring step
- Parameter index aggregates shader/tone/haptic inputs for downstream wiring (labs/generator/assembler.py:64; tests/test_generator_assembler.py:23)
- Control mappings prune dangling references and mirror the parameter index (labs/generator/assembler.py:66; labs/generator/assembler.py:118)
- Provenance records assembler version, timestamp, and deterministic IDs when seeded (labs/generator/assembler.py:70; labs/generator/assembler.py:94; labs/agents/generator.py:50)

## Patch lifecycle
- Preview logs patch diffs without mutating the asset (labs/patches.py:18; tests/test_patches.py:11)
- Apply merges updates, invokes CriticAgent, and logs review payloads (labs/patches.py:37; tests/test_patches.py:25)
- Rate records critic rating stubs and lifecycle entries for RLHF prep (labs/patches.py:68; labs/agents/critic.py:170; tests/test_patches.py:54)

## MCP integration
- STDIO validator requires MCP_ADAPTER_CMD and propagates missing adapter failures (labs/mcp_stdio.py:145; tests/test_critic.py:120)
- TCP is the default when MCP_ENDPOINT is unset/invalid and requires host/port wiring (labs/mcp_stdio.py:129; labs/mcp_stdio.py:170; tests/test_tcp.py:163)
- Socket transport is optional and documented via LABS_SOCKET_TESTS gate with explicit failure detail (tests/test_socket.py:9; tests/test_critic.py:186)
- 1 MiB payload cap enforced across transports and exercised in tests (labs/transport.py:8; tests/test_tcp.py:110; tests/test_socket.py:46)
- Strict vs relaxed modes both attempt MCP validation while logging warnings vs errors (labs/agents/critic.py:63; tests/test_pipeline.py:154)
- Resolver fallback behaviour locked by unit tests (labs/mcp_stdio.py:129; tests/test_tcp.py:171)
- SYN_SCHEMAS_DIR still forwards without emitting the required deprecation warning (docs/labs_spec.md:175; labs/mcp_stdio.py:152)

## External generator integration
- Gemini/OpenAI implementations reuse ExternalGenerator with provenance trace IDs and MCP results (labs/generator/external.py:115; tests/test_pipeline.py:211)
- CLI engine flag selects integrations while falling back to local generator when unset (labs/cli.py:82; labs/cli.py:108)
- LABS_EXTERNAL_LIVE toggles mock vs live mode defaults for deterministic tests (labs/generator/external.py:61; tests/test_external_generator.py:16)
- Successful runs log request/response payloads, MCP review, and experiment paths (labs/generator/external.py:168; tests/test_external_generator.py:36)
- Transport failures capture attempt traces with structured reason/detail metadata (labs/generator/external.py:197; tests/test_external_generator.py:52)

## Test coverage
| Feature | Tested? | Evidence |
| --- | --- | --- |
| Generator→Critic pipeline and persistence | Yes | tests/test_pipeline.py:12; tests/test_pipeline.py:93 |
| CLI relaxed mode warning path | Yes | tests/test_pipeline.py:154; tests/test_pipeline.py:183 |
| Patch lifecycle preview/apply/rate | Yes | tests/test_patches.py:11; tests/test_patches.py:43 |
| External generator success + failure logging | Yes | tests/test_pipeline.py:191; tests/test_external_generator.py:52 |
| resolve_mcp_endpoint fallback to TCP | Yes | tests/test_tcp.py:163; tests/test_tcp.py:171 |
| Critic socket_unavailable detail | Yes | tests/test_critic.py:186 |
| Transport payload cap enforcement | Yes | tests/test_tcp.py:110; tests/test_socket.py:46 |

## Dependencies and runtime
| Package | Used in | Required/Optional |
| --- | --- | --- |
| pytest>=7.0 | tests/* CI suite | Required (dev/test) |

## Environment variables
- `MCP_ENDPOINT` defaults to TCP and rejects invalid values by falling back (labs/mcp_stdio.py:129; tests/test_tcp.py:171)
- `MCP_HOST` / `MCP_PORT` provide TCP endpoint defaults and validation (labs/mcp_stdio.py:170; .env:7)
- `MCP_ADAPTER_CMD` is mandatory for STDIO runs and surfaces outages (labs/mcp_stdio.py:145; tests/test_critic.py:120)
- `MCP_SOCKET_PATH` controls socket transport and errors when unset (labs/mcp_stdio.py:159; tests/test_critic.py:186)
- `LABS_FAIL_FAST` toggles strict vs relaxed severity while still attempting validation (labs/agents/critic.py:21; tests/test_pipeline.py:154)
- `LABS_EXPERIMENTS_DIR` redirects persisted assets/logs for CLI runs (labs/cli.py:20; tests/test_pipeline.py:95)
- `LABS_EXTERNAL_LIVE` switches external generators between mock and live modes (labs/generator/external.py:61; tests/test_external_generator.py:52)
- `LABS_SOCKET_TESTS` guards optional Unix socket tests (tests/test_socket.py:9)
- `GEMINI_MODEL` / `OPENAI_MODEL` / `OPENAI_TEMPERATURE` thread through external defaults (labs/generator/external.py:347; labs/generator/external.py:399)
- `SYN_SCHEMAS_DIR` is still forwarded to STDIO without the required warning and is not labelled deprecated in .env (labs/mcp_stdio.py:152; .env:23)

## Logging
- `log_jsonl` ensures directories exist and writes deterministic JSONL entries (labs/logging.py:13)
- Generator proposes assets and experiment records to meta/output/labs/generator.jsonl (labs/agents/generator.py:60; labs/agents/generator.py:98)
- Critic review and rating stubs append to meta/output/labs/critic.jsonl with reason/detail fields (labs/agents/critic.py:166; labs/agents/critic.py:191)
- Patch lifecycle writes preview/apply/rate events to meta/output/labs/patches.jsonl (labs/patches.py:18; labs/patches.py:82)
- External generators log successful runs and failures with structured metadata (labs/generator/external.py:168; labs/generator/external.py:214; tests/test_external_generator.py:52)

## Documentation accuracy
- README documents TCP as default, fallback behaviour, and socket optionality (README.md:31; README.md:45; README.md:57)
- README and spec both acknowledge SYN_SCHEMAS_DIR deprecation but the live .env sample contradicts the policy (docs/labs_spec.md:174; README.md:47; .env:23)
- Maintainer process doc lacks a reference to resolve_mcp_endpoint despite the spec requirement (docs/labs_spec.md:164; docs/process.md:1)

## Detected divergences
- SYN_SCHEMAS_DIR forwarding lacks the mandated deprecation warning when STDIO is selected (docs/labs_spec.md:175; labs/mcp_stdio.py:152)
- Committed .env sample still promotes SYN_SCHEMAS_DIR instead of flagging it as deprecated STDIO-only (docs/labs_spec.md:174; .env:23)
- Maintainer documentation omits the resolver fallback guidance required for future agents (docs/labs_spec.md:164; docs/process.md:1)

## Recommendations
- Add a logger.warning emission inside the STDIO branch of build_validator_from_env when SYN_SCHEMAS_DIR is detected, satisfying the spec’s deprecation logging rule (docs/labs_spec.md:175; labs/mcp_stdio.py:152)
- Update .env to mark SYN_SCHEMAS_DIR as deprecated/STDIO-only or remove it entirely, keeping samples aligned with the documented environment defaults (docs/labs_spec.md:174; .env:23)
- Amend docs/process.md (or another maintainer guide) to mention resolve_mcp_endpoint so transport provenance decisions remain documented (docs/labs_spec.md:164; docs/process.md:1)
