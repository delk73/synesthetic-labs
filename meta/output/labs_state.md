# Synesthetic Labs State (v0.3.3 Audit)
## Summary of repo state
- GeneratorAgent and AssetAssembler produce canonical assets, prune control mappings, and log proposals under `meta/output/labs/generator.jsonl` (labs/agents/generator.py:37; labs/generator/assembler.py:64; tests/test_generator.py:10)
- Critic review enforces required fields, handles strict vs relaxed MCP validation, and records reviews and ratings (labs/agents/critic.py:46; labs/agents/critic.py:148; tests/test_critic.py:161)
- MCP resolver defaults to TCP and gates STDIO/socket options while forwarding deprecated schemas only for STDIO with a warning (labs/mcp_stdio.py:134; labs/mcp_stdio.py:150; tests/test_critic.py:203)
- External generator integrations add provenance, retries, and log MCP-reviewed runs to the external stream (labs/generator/external.py:97; labs/generator/external.py:168; tests/test_external_generator.py:36)
- Spec logging metadata (trace_id, transport, mode) is missing from generator/critic/patch entries, leaving a compliance gap (docs/labs_spec.md:206; labs/agents/critic.py:148; labs/patches.py:57)

## Top gaps & fixes (3-5 bullets)
- Generate and persist a `trace_id` per generator/critic/patch log entry to satisfy the spec metadata contract; current records contain no identifier (docs/labs_spec.md:206; labs/agents/generator.py:61; labs/patches.py:57; tests/test_generator.py:32)
- Include explicit strict/relaxed mode and resolved MCP transport fields in review and patch logs so auditors can confirm runtime behavior (docs/labs_spec.md:206; labs/agents/critic.py:148; tests/test_patches.py:49)
- Extend `GeneratorAgent.record_experiment` to attach structured failure reason/detail instead of only copying issue strings to generator.jsonl (docs/labs_spec.md:206; labs/agents/generator.py:82; tests/test_pipeline.py:139)

## Alignment with labs_spec.md (table: Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| --- | --- | --- |
| Generator assembles canonical shader/tone/haptic sections | Present | labs/generator/assembler.py:56; tests/test_generator_components.py:22 |
| TCP default transport with STDIO/socket options | Present | labs/mcp_stdio.py:134; labs/mcp_stdio.py:171; tests/test_tcp.py:140 |
| Resolver falls back to TCP on unset/invalid endpoint | Present | labs/mcp_stdio.py:134; tests/test_tcp.py:163 |
| 1 MiB payload cap with oversize handling | Present | labs/transport.py:20; tests/test_tcp.py:110 |
| SYN_SCHEMAS_DIR forwarded once with deprecation warning | Present | labs/mcp_stdio.py:160; tests/test_critic.py:203 |
| Critic surfaces socket_unavailable detail | Present | tests/test_critic.py:187 |
| Strict vs relaxed modes still invoke MCP | Present | labs/agents/critic.py:63; tests/test_pipeline.py:152 |
| External generator runs validated with provenance logs | Present | labs/generator/external.py:168; tests/test_external_generator.py:36 |
| Logging entries include trace_id + mode + transport metadata | Missing | docs/labs_spec.md:206; labs/agents/critic.py:148; labs/patches.py:57 |

## Generator implementation (table: Component → Status → Evidence)
| Component | Status | Evidence |
| --- | --- | --- |
| Proposal logging & provenance | Present | labs/agents/generator.py:37; tests/test_generator.py:10 |
| Deterministic IDs via seed | Present | labs/generator/assembler.py:94; tests/test_determinism.py:7 |
| Control pruning & parameter index | Present | labs/generator/assembler.py:64; tests/test_generator_assembler.py:15 |
| Experiment log carries structured failure metadata | Divergent | docs/labs_spec.md:206; labs/agents/generator.py:82 |

## Critic implementation (table: Responsibility → Status → Evidence)
| Responsibility | Status | Evidence |
| --- | --- | --- |
| Required field validation | Present | labs/agents/critic.py:58; tests/test_critic.py:13 |
| Fail-fast vs relaxed handling | Present | labs/agents/critic.py:63; tests/test_critic.py:161 |
| Transport-specific error reason/detail | Present | labs/agents/critic.py:70; tests/test_critic.py:187 |
| Review log includes mode/transport metadata | Missing | docs/labs_spec.md:206; labs/agents/critic.py:148 |
| Rating stub logging | Present | labs/agents/critic.py:170; tests/test_ratings.py:10 |

## Assembler / Wiring step (bullets: parameter index, dangling reference pruning, provenance)
- Collects shader/tone/haptic parameters for downstream wiring (labs/generator/assembler.py:64)
- Prunes control mappings that target missing parameters before persistence (labs/generator/assembler.py:115; tests/test_generator_components.py:38)
- Provenance captures deterministic IDs and timestamps when seeds are supplied (labs/generator/assembler.py:94; tests/test_determinism.py:7)

## Patch lifecycle (bullets: preview, apply, rate stubs, logging)
- Preview logs patch diffs without mutating the asset (labs/patches.py:18; tests/test_patches.py:11)
- Apply merges updates, revalidates via CriticAgent, and records the review payload (labs/patches.py:37; tests/test_patches.py:25)
- Rate delegates to critic rating stubs and logs lifecycle plus critic records (labs/patches.py:68; tests/test_patches.py:59)

## MCP integration (bullets: STDIO, TCP-default, socket-optional validation; failure handling; strict vs relaxed mode; 1 MiB caps; reason/detail logging; resolver fallback)
- TCP remains the default transport with host/port env controls (labs/mcp_stdio.py:134; labs/mcp_stdio.py:182; tests/test_tcp.py:140)
- STDIO requires `MCP_ADAPTER_CMD`, normalizes the deprecated schema override once, and warns maintainers (labs/mcp_stdio.py:150; labs/mcp_stdio.py:160; tests/test_critic.py:203)
- Socket transport is optional; missing socket paths surface `socket_unavailable` detail (labs/mcp_stdio.py:171; tests/test_critic.py:187)
- Transport helpers enforce the 1 MiB cap and propagate oversize errors (labs/transport.py:20; tests/test_tcp.py:110)
- Critic resolves the transport per review, attempts validation in both strict and relaxed modes, and logs reason/detail (labs/agents/critic.py:63; tests/test_pipeline.py:152)

## External generator integration (bullets: Gemini/OpenAI interface, provenance logging, CLI flags, error handling, MCP-enforced validation)
- Gemini/OpenAI classes normalise assets, inject provenance, and honour default parameters (labs/generator/external.py:115; labs/generator/external.py:349; tests/test_external_generator.py:16)
- CLI engine flag routes external runs through critic validation and experiment persistence (labs/cli.py:108; labs/cli.py:141; tests/test_pipeline.py:211)
- Retry/backoff surfaces structured failure metadata when transports fail (labs/generator/external.py:97; labs/generator/external.py:197; tests/test_external_generator.py:52)
- `record_run` appends MCP review results and validation status to external.jsonl (labs/generator/external.py:168; tests/test_external_generator.py:36)

## Test coverage (table: Feature → Tested? → Evidence, including socket failure coverage and resolver fallback)
| Feature | Tested? | Evidence |
| --- | --- | --- |
| Generator deterministic wiring & pruning | Yes | tests/test_determinism.py:7; tests/test_generator_assembler.py:15 |
| Critic strict vs relaxed MCP handling | Yes | tests/test_critic.py:161; tests/test_pipeline.py:152 |
| TCP default, oversize, and fallback behaviour | Yes | tests/test_tcp.py:110; tests/test_tcp.py:140; tests/test_tcp.py:163 |
| Socket failure surfaces socket_unavailable detail | Yes | tests/test_critic.py:187 |
| SYN_SCHEMAS_DIR warning emitted once | Yes | tests/test_critic.py:203 |
| External generator provenance & failure logging | Yes | tests/test_external_generator.py:36; tests/test_external_generator.py:52 |
| Patch lifecycle logging | Yes | tests/test_patches.py:25; tests/test_patches.py:59 |

## Dependencies and runtime (table: Package → Used in → Required/Optional)
| Package | Used in | Required/Optional |
| --- | --- | --- |
| pytest | tests/* | Optional (dev) | requirements.txt:1 |

## Environment variables (bullets: name, default, transport defaults, behavior when MCP/external API unreachable, deprecated knobs)
- `MCP_ENDPOINT`: Selects the validator transport and falls back to TCP when unset or invalid (labs/mcp_stdio.py:134; tests/test_tcp.py:163)
- `MCP_HOST` / `MCP_PORT`: Default to `127.0.0.1:8765` for TCP and must be set when overriding (labs/mcp_stdio.py:183)
- `MCP_ADAPTER_CMD`: Required for STDIO adapters; optional `SYN_SCHEMAS_DIR` is forwarded with a single deprecation warning (labs/mcp_stdio.py:150; labs/mcp_stdio.py:160)
- `MCP_SOCKET_PATH`: Required when using the socket transport (labs/mcp_stdio.py:171)
- `LABS_FAIL_FAST`: Controls strict vs relaxed critic behavior (labs/agents/critic.py:21; tests/test_critic.py:161)
- `LABS_EXPERIMENTS_DIR`: Overrides the experiment persistence directory (labs/cli.py:34; tests/test_pipeline.py:93)
- `LABS_EXTERNAL_LIVE`, `GEMINI_MODEL`, `OPENAI_MODEL`, `OPENAI_TEMPERATURE`: Configure external generator live mode and parameters (labs/generator/external.py:61; labs/generator/external.py:399)
- `LABS_SOCKET_TESTS`: Opts into Unix socket transport tests when supported (tests/test_socket.py:12)
- `SYN_SCHEMAS_DIR`: Deprecated STDIO-only schema override retained for adapters (labs/mcp_stdio.py:157; .example.env:13)

## Logging (bullets: structured JSONL, provenance fields, patch/rating/external fields, reason/detail on transport failures, location under meta/output/)
- `log_jsonl` ensures append-only JSONL with timestamp defaults and shared output roots under `meta/output` (labs/logging.py:13; tests/test_logging.py:10)
- Generator, critic, patch, and external streams append assets, reviews, ratings, and MCP responses as they run (labs/agents/generator.py:61; labs/agents/critic.py:166; labs/patches.py:33; labs/generator/external.py:195)
- Spec-mandated trace_id, mode, and transport metadata are absent from generator/critic/patch entries, so failure analysis lacks the required context (docs/labs_spec.md:206; tests/test_generator.py:32; tests/test_patches.py:49)

## Documentation accuracy (bullets: README vs. labs_spec.md; TCP as default, socket optional; maintainer docs reference resolver; env cleanup)
- README documents TCP as the default, socket optional workflow, and fallback behaviour (README.md:31; README.md:45; README.md:58)
- README marks `SYN_SCHEMAS_DIR` as deprecated and STDIO-only (README.md:47)
- `.example.env` reflects TCP defaults and the deprecated schema override note ( .example.env:1; .example.env:13)
- Maintainer process docs direct teams to the resolver and associated tests for provenance (docs/process.md:41)

## Detected divergences
- Generator, critic, and patch logs omit spec-required trace_id and mode/transport metadata (docs/labs_spec.md:206; labs/agents/critic.py:148; labs/patches.py:57)
- Generator experiment records lack structured failure reason/detail fields despite the logging contract (docs/labs_spec.md:206; labs/agents/generator.py:82)

## Recommendations
- Augment generator/critic/patch logging to emit trace_id, resolved transport, and strict/relaxed mode, and extend tests to assert the metadata (docs/labs_spec.md:206; labs/agents/critic.py:148; tests/test_patches.py:49)
- Enhance `GeneratorAgent.record_experiment` to persist `validation_error` reason/detail (and add coverage) so generator.jsonl aligns with the spec (docs/labs_spec.md:206; labs/agents/generator.py:82; tests/test_pipeline.py:139)
- Factor shared logging helpers that stamp the new metadata to avoid drift across streams (labs/logging.py:13; labs/patches.py:57)
