# Synesthetic Labs State (v0.3.3 Audit)
## Summary of repo state
- GeneratorAgent and AssetAssembler produce deterministic assets, prune dangling controls, and log JSONL outputs for CLI + experiments (labs/agents/generator.py:37; labs/generator/assembler.py:64; tests/test_pipeline.py:15)
- Critic enforces required fields, fail-fast vs relaxed MCP handling, and records reviews/ratings to meta/output/labs/critic.jsonl (labs/agents/critic.py:63; labs/agents/critic.py:148; tests/test_critic.py:23)
- MCP transports default to TCP with STDIO/socket adapters sharing 1 MiB caps and resolver fallback coverage (labs/mcp_stdio.py:134; labs/transport.py:8; tests/test_tcp.py:140)
- External generators capture provenance, MCP results, and failure traces in shared JSONL sinks (labs/generator/external.py:168; labs/logging.py:30; tests/test_external_generator.py:16)

## Top gaps & fixes (3-5 bullets)
- Clarify in README that the deprecated SYN_SCHEMAS_DIR override only applies to STDIO adapters to mirror the spec language (docs/labs_spec.md:174; README.md:47)
- Mirror the STDIO-only deprecation note inside .example.env so sample envs stay aligned with the transport policy (docs/labs_spec.md:174; .example.env:13)
- Add a regression test that sets SYN_SCHEMAS_DIR under STDIO and asserts the warning emits once to guard the deprecation contract (docs/labs_spec.md:175; labs/mcp_stdio.py:160; tests/test_critic.py:96)

## Alignment with labs_spec.md (table: Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| --- | --- | --- |
| TCP default transport with fallback | Present | labs/mcp_stdio.py:134; tests/test_tcp.py:140 |
| STDIO/TCP/socket validators from env | Present | labs/mcp_stdio.py:150; labs/mcp_stdio.py:171; labs/mcp_stdio.py:182 |
| MCP validation runs in strict and relaxed modes | Present | labs/agents/critic.py:63; tests/test_pipeline.py:63; tests/test_pipeline.py:152 |
| Failure logging includes reason/detail | Present | labs/agents/critic.py:70; tests/test_critic.py:55 |
| 1 MiB payload cap enforced across transports | Present | labs/transport.py:8; tests/test_tcp.py:120 |
| External generator provenance and MCP result logged | Present | labs/generator/external.py:168; tests/test_pipeline.py:191 |
| Socket optional with failure coverage | Present | README.md:57; tests/test_critic.py:186 |
| resolve_mcp_endpoint fallback tested | Present | labs/mcp_stdio.py:134; tests/test_tcp.py:163 |
| SYN_SCHEMAS_DIR warning emitted on STDIO forwarding | Present | labs/mcp_stdio.py:160; docs/labs_spec.md:175 |
| README marks SYN_SCHEMAS_DIR deprecated + STDIO-only | Divergent | docs/labs_spec.md:174; README.md:47 |

## Generator implementation (table: Component → Status → Evidence)
| Component | Status | Evidence |
| --- | --- | --- |
| GeneratorAgent provenance + JSONL logging | Present | labs/agents/generator.py:37; tests/test_generator.py:9 |
| AssetAssembler deterministic wiring | Present | labs/generator/assembler.py:44; tests/test_determinism.py:7 |
| Parameter index aggregation and control pruning | Present | labs/generator/assembler.py:64; tests/test_generator_assembler.py:11 |
| Experiment logging after validation | Present | labs/agents/generator.py:64; tests/test_pipeline.py:93 |
| CLI experiment persistence | Present | labs/cli.py:135; tests/test_pipeline.py:93 |

## Critic implementation (table: Responsibility → Status → Evidence)
| Responsibility | Status | Evidence |
| --- | --- | --- |
| Required field checks and issue list | Present | labs/agents/critic.py:58; tests/test_critic.py:23 |
| Strict vs relaxed MCP handling | Present | labs/agents/critic.py:63; tests/test_pipeline.py:63; tests/test_pipeline.py:152 |
| Transport-specific reason/detail payloads | Present | labs/agents/critic.py:70; tests/test_critic.py:55 |
| Review JSONL logging | Present | labs/agents/critic.py:148; labs/logging.py:13 |
| Rating stub logging | Present | labs/agents/critic.py:180; tests/test_ratings.py:10 |

## Assembler / Wiring step (bullets: parameter index, dangling reference pruning, provenance)
- Parameter index collects shader/tone/haptic inputs for downstream wiring (labs/generator/assembler.py:64; tests/test_generator_assembler.py:17)
- Control mappings prune dangling parameters before persistence (labs/generator/assembler.py:115; tests/test_generator_components.py:44)
- Provenance captures assembler version, timestamps, and deterministic IDs under seeds (labs/generator/assembler.py:70; labs/generator/assembler.py:94; tests/test_determinism.py:7)

## Patch lifecycle (bullets: preview, apply, rate stubs, logging)
- Preview logs patch diffs without mutation and writes to meta/output/labs/patches.jsonl (labs/patches.py:18; tests/test_patches.py:11)
- Apply merges updates, revalidates via CriticAgent, and records reviews in the patch log (labs/patches.py:37; tests/test_patches.py:25)
- Rate invokes critic rating stubs and logs lifecycle + critic entries for RLHF readiness (labs/patches.py:68; labs/agents/critic.py:180; tests/test_patches.py:54)

## MCP integration (bullets: STDIO, TCP-default, socket-optional validation; failure handling; strict vs relaxed mode; 1 MiB caps; reason/detail logging; resolver fallback)
- STDIO validator requires MCP_ADAPTER_CMD, normalizes SYN_SCHEMAS_DIR, and warns once when forwarding the deprecated override (labs/mcp_stdio.py:150; labs/mcp_stdio.py:160)
- TCP remains the default when MCP_ENDPOINT is unset/invalid and mandates host/port wiring (labs/mcp_stdio.py:134; labs/mcp_stdio.py:182; tests/test_tcp.py:140)
- Socket transport enforces MCP_SOCKET_PATH and surfaces socket_unavailable detail on failure (labs/mcp_stdio.py:171; tests/test_critic.py:186)
- Shared transport helpers enforce the 1 MiB cap and propagate oversize errors (labs/transport.py:8; tests/test_tcp.py:120)
- Critic emits reason/detail per transport and honors fail-fast vs relaxed modes without skipping validation (labs/agents/critic.py:63; labs/agents/critic.py:70; tests/test_pipeline.py:63)
- Resolver fallback is exercised by unit tests to prevent drift (labs/mcp_stdio.py:134; tests/test_tcp.py:163)

## External generator integration (bullets: Gemini/OpenAI interface, provenance logging, CLI flags, error handling, MCP-enforced validation)
- Gemini and OpenAI generators inject engine/api_version/trace_id provenance while normalising canonical sections (labs/generator/external.py:115; labs/generator/external.py:304; tests/test_external_generator.py:16)
- CLI `generate --engine` path persists MCP-reviewed runs and appends records to external.jsonl (labs/cli.py:191; labs/generator/external.py:168; tests/test_pipeline.py:191)
- Retries capture per-attempt traces and record structured failure metadata on exhaustion (labs/generator/external.py:147; labs/generator/external.py:214; tests/test_external_generator.py:52)
- External runs always route through CriticAgent for MCP validation before persistence (labs/cli.py:131; tests/test_pipeline.py:191)

## Test coverage (table: Feature → Tested? → Evidence, including socket failure coverage and resolver fallback)
| Feature | Tested? | Evidence |
| --- | --- | --- |
| Generator→Critic pipeline logging and validation | Yes | tests/test_pipeline.py:15 |
| CLI fail-fast vs relaxed handling | Yes | tests/test_pipeline.py:63; tests/test_pipeline.py:152 |
| TCP default + fallback | Yes | tests/test_tcp.py:140 |
| 1 MiB payload cap enforcement | Yes | tests/test_tcp.py:120 |
| Socket failure surfaces socket_unavailable detail | Yes | tests/test_critic.py:186 |
| resolve_mcp_endpoint fallback | Yes | tests/test_tcp.py:163 |
| External generator provenance + logging | Yes | tests/test_external_generator.py:16 |
| Patch lifecycle logging | Yes | tests/test_patches.py:11 |
| SYN_SCHEMAS_DIR deprecation warning | No | labs/mcp_stdio.py:160; tests/test_critic.py:96 |

## Dependencies and runtime (table: Package → Used in → Required/Optional)
| Package | Used in | Required/Optional |
| --- | --- | --- |
| pytest | Test runner for the suite | Optional (requirements.txt:1; tests/test_pipeline.py:1) |

## Environment variables (bullets: name, default, transport defaults, behavior when MCP/external API unreachable, deprecated knobs)
- MCP_ENDPOINT: selects transport and falls back to `tcp` when unset/invalid (labs/mcp_stdio.py:134; tests/test_tcp.py:163)
- MCP_HOST / MCP_PORT: required when using the TCP default transport (labs/mcp_stdio.py:182; .env:7)
- MCP_ADAPTER_CMD: mandatory for STDIO validation; missing command raises MCPUnavailableError (labs/mcp_stdio.py:151; tests/test_critic.py:120)
- MCP_SOCKET_PATH: required for socket transport and validated via normalize_resource_path (labs/mcp_stdio.py:171; tests/test_critic.py:186)
- SYN_SCHEMAS_DIR: deprecated STDIO-only override that logs a warning before forwarding (labs/mcp_stdio.py:160; .env:23)
- LABS_FAIL_FAST: toggles strict vs relaxed MCP failure handling (labs/agents/critic.py:63; README.md:47)
- LABS_EXPERIMENTS_DIR: customises persisted experiment output location (labs/cli.py:28; tests/test_pipeline.py:93)
- LABS_EXTERNAL_LIVE / GEMINI_MODEL / OPENAI_MODEL / OPENAI_TEMPERATURE: configure external generator transport and parameters (labs/generator/external.py:102; labs/generator/external.py:186; README.md:85)
- LABS_SOCKET_TESTS: opt-in guard for Unix socket tests in environments that support them (README.md:57; tests/test_socket.py:9)

## Logging (bullets: structured JSONL, provenance fields, patch/rating/external fields, reason/detail on transport failures, location under meta/output/)
- log_jsonl appends deterministic JSON lines for generator, critic, patch, and external sinks under meta/output/labs (labs/logging.py:13; tests/test_logging.py:10)
- Critic review entries persist validation_error reason/detail to trace MCP outages (labs/agents/critic.py:70; tests/test_critic.py:55)
- External generator record_run/record_failure include trace_id, requests/responses, and failure reason/detail (labs/generator/external.py:168; labs/generator/external.py:214; tests/test_external_generator.py:52)
- Patch lifecycle actions log preview/apply/rate records alongside critic rating stubs (labs/patches.py:33; tests/test_patches.py:25)

## Documentation accuracy (bullets: README vs. labs_spec.md; TCP as default, socket optional; maintainer docs reference resolver; env cleanup)
- README documents TCP as default, optional STDIO/socket transports, and socket test opt-in (README.md:31; README.md:57)
- README flags SYN_SCHEMAS_DIR as deprecated but omits the STDIO-only qualifier mandated by the spec (README.md:47; docs/labs_spec.md:174)
- Maintainer process notes reference resolve_mcp_endpoint for transport provenance (docs/process.md:41)
- .env sample marks SYN_SCHEMAS_DIR as deprecated and STDIO-only (.env:23)

## Detected divergences
- README environment guidance does not state that deprecated SYN_SCHEMAS_DIR is limited to STDIO adapters (docs/labs_spec.md:174; README.md:47)
- .example.env still lists SYN_SCHEMAS_DIR without the STDIO-only qualifier, risking reintroduction in non-STDIO scenarios (docs/labs_spec.md:174; .example.env:13)

## Recommendations
- Update README to add the STDIO-only wording for SYN_SCHEMAS_DIR, matching the spec’s deprecation policy (docs/labs_spec.md:174; README.md:47)
- Revise .example.env with the same STDIO-only deprecation note so sample configs stay compliant (docs/labs_spec.md:174; .example.env:13)
- Introduce a unit test that sets SYN_SCHEMAS_DIR for STDIO, asserts the warning via caplog, and confirms only one emission (docs/labs_spec.md:175; labs/mcp_stdio.py:160; tests/test_critic.py:96)
