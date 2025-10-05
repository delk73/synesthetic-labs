# Summary of repo state
- Generator defaults to schema version 0.7.3, branches between legacy and enriched payloads, and stamps the hosted `$schema` URL while wiring provenance and section pruning through the assembler stack.【F:labs/generator/assembler.py†L23-L386】【F:tests/test_generator_assembler.py†L19-L76】
- External generators satisfy the v0.3.4 live-call contract with env-driven credentials, redacted headers, retry/backoff, normalization, and JSONL provenance logging that captures schema_version and `$schema`.【F:labs/generator/external.py†L25-L678】【F:labs/generator/external.py†L311-L372】【F:tests/test_external_generator.py†L27-L345】
- Critic strict mode reports MCP outages, but the relaxed path suppresses validator calls, returns `ok`, and the CLI persists assets despite no MCP validation, diverging from the spec requirement to always validate against the declared schema.【F:labs/agents/critic.py†L115-L188】【F:tests/test_pipeline.py†L171-L207】【F:docs/labs_spec.md†L29-L109】

# Top gaps & fixes
- Rework relaxed-mode review to invoke MCP even when `build_validator_from_env` initially fails so validation always runs against the declared schema version before marking success.【F:labs/agents/critic.py†L130-L172】【F:docs/labs_spec.md†L29-L109】
- Gate CLI persistence on confirmed MCP execution (e.g., require `mcp_response` or a flag) to avoid saving assets when validation was skipped in relaxed mode.【F:labs/cli.py†L160-L189】【F:tests/test_pipeline.py†L171-L207】
- Add regression tests covering relaxed-mode MCP invocation/persistence rules once the critic/CLI changes land.【F:tests/test_pipeline.py†L197-L207】

# Alignment with labs_spec.md
| Spec item | Status | Evidence |
| --- | --- | --- |
| Generator branches on schema_version, emits `$schema`, and toggles legacy/enriched fields.【F:docs/labs_spec.md†L29-L99】 | Present | AssetAssembler builds 0.7.3 vs 0.7.4 payloads with appropriate sections and provenance, with unit coverage.【F:labs/generator/assembler.py†L23-L386】【F:tests/test_generator_assembler.py†L19-L76】 |
| CLI exposes `--schema-version` overriding env/default precedence.【F:docs/labs_spec.md†L56-L66】 | Present | CLI argument default ties to env/default and tests assert precedence through external generator wrapping.【F:labs/cli.py†L83-L199】【F:tests/test_pipeline.py†L300-L360】 |
| Always run MCP validation against declared schema.【F:docs/labs_spec.md†L29-L109】 | Divergent | Critic relaxed mode skips validator invocation and still reports success/persists experiments.【F:labs/agents/critic.py†L130-L188】【F:tests/test_pipeline.py†L197-L207】 |
| External logging must carry schema_version and `$schema`.【F:docs/labs_spec.md†L113-L134】 | Present | `record_run` writes schema_version/`$schema` and tests assert the JSONL payload.【F:labs/generator/external.py†L311-L356】【F:tests/test_external_generator.py†L53-L76】 |

# Generator implementation
| Component | Status | Evidence |
| --- | --- | --- |
| Assembler defaults to 0.7.3 and prunes wiring before branching legacy/enriched output.| Present | Branch logic sets `$schema`, parameter index, and provenance for both schema families.【F:labs/generator/assembler.py†L67-L386】 |
| GeneratorAgent logging and experiment recording capture schema_version, transport, strict flag, and failure metadata.| Present | Propose/record_experiment set trace_id, transport, validation info, and failure records.【F:labs/agents/generator.py†L54-L199】 |
| CLI deterministic flow respects schema flag/env precedence.| Present | `labs.cli` constructs GeneratorAgent with requested schema_version and persists experiments with relative paths.【F:labs/cli.py†L130-L189】【F:tests/test_pipeline.py†L120-L168】 |

# Critic implementation
| Responsibility | Status | Evidence |
| --- | --- | --- |
| Strict mode fails when MCP unavailable, logging `mcp_unavailable` taxonomy.| Present | Fail-fast path raises failure payloads and tests assert stdio/socket/tcp error detail.【F:labs/agents/critic.py†L130-L188】【F:tests/test_critic.py†L162-L201】 |
| Relaxed mode should still run MCP but downgrade outages.| Divergent | Critic sets `should_attempt_validation=False` and returns `ok` without contacting MCP when builder fails.【F:labs/agents/critic.py†L130-L172】【F:tests/test_pipeline.py†L197-L207】 |
| Rating stubs inherit transport/strict metadata.| Present | `record_rating` logs mode/transport with trace IDs and tests confirm log propagation.【F:labs/agents/critic.py†L223-L250】【F:tests/test_patches.py†L65-L92】 |

# Assembler / Wiring step
- Parameter index collected from shader/tone/haptic inputs and deduplicated before enriched emission.【F:labs/generator/assembler.py†L83-L262】
- Control mappings pruned to known parameters to avoid dangling references.【F:labs/generator/assembler.py†L83-L417】
- Meta/provenance blocks seeded with deterministic identifiers, assembler version, and generator metadata per schema family.【F:labs/generator/assembler.py†L95-L304】

# Patch lifecycle
- `preview_patch` logs trace_id, strict flag, mode, and transport for dry runs with tests asserting JSONL content.【F:labs/patches.py†L33-L62】【F:tests/test_patches.py†L11-L28】
- `apply_patch` updates assets, routes through Critic, records failure detail when validation fails, and persists transport/strict metadata.【F:labs/patches.py†L64-L117】【F:tests/test_patches.py†L31-L63】
- `rate_patch` stores critic rating stubs alongside transport/mode data for downstream RLHF alignment.【F:labs/patches.py†L119-L158】【F:tests/test_patches.py†L65-L92】

# MCP integration
- STDIO, socket, and TCP validators constructed via `build_validator_from_env`, with TCP as fallback when endpoint unset/invalid.【F:labs/mcp_stdio.py†L162-L231】【F:tests/test_tcp.py†L175-L188】
- Validators enforce 1 MiB caps and decode via shared transport helpers, raising `MCPUnavailableError` on framing issues.【F:labs/mcp_stdio.py†L178-L229】【F:labs/mcp/tcp_client.py†L18-L56】【F:labs/transport.py†L1-L68】
- Socket transport exposes `socket_unavailable` detail when path missing, covered in critic tests.【F:labs/mcp_stdio.py†L199-L208】【F:tests/test_critic.py†L188-L201】
- Resolver fallback emits STDIO deprecation warning once for `SYN_SCHEMAS_DIR` with test coverage.【F:labs/mcp_stdio.py†L184-L197】【F:tests/test_critic.py†L204-L217】

# External generator integration
- Gemini/OpenAI builders pull credentials/model defaults from env, branch mock/live transports, and share normalization pipelines.【F:labs/generator/external.py†L108-L123】【F:labs/generator/external.py†L1008-L1188】
- Live calls inject redacted `Authorization` headers, enforce size caps, and classify HTTP/URL errors for retry taxonomy.【F:labs/generator/external.py†L472-L538】【F:tests/test_external_generator.py†L130-L214】
- CLI flags for temperature/timeout propagate into external parameter envelopes with precedence tests verifying seed/timeout/schema propagation.【F:labs/cli.py†L130-L143】【F:tests/test_pipeline.py†L300-L360】
- MCP validation results recorded into external.jsonl alongside normalized assets and failure metadata.【F:labs/generator/external.py†L311-L356】【F:tests/test_external_generator.py†L53-L113】

# External generation LIVE (v0.3.4)
- Env keys (`LABS_EXTERNAL_LIVE`, provider API keys/endpoints/models) control live enablement and defaults.【F:labs/generator/external.py†L126-L179】【F:.example.env†L21-L29】
- Endpoint resolution enforces presence, builds headers with `Authorization`, redacts logs, and returns failure taxonomy when missing.【F:labs/generator/external.py†L472-L489】【F:tests/test_external_generator.py†L130-L162】
- Timeout/backoff implemented with exponential jitter and retry classification for rate limits vs auth errors.【F:labs/generator/external.py†L453-L470】【F:tests/test_external_generator.py†L236-L279】
- Request/response size guards raise `bad_response` errors, with tests for 256KiB/1MiB enforcement.【F:labs/generator/external.py†L507-L538】【F:tests/test_external_generator.py†L195-L234】
- Normalization rejects unknown keys, wrong types, and out-of-range parameters before MCP validation.【F:labs/generator/external.py†L680-L828】【F:tests/test_external_generator.py†L282-L384】

# Test coverage
| Feature | Tested? | Evidence |
| --- | --- | --- |
| Assembler legacy/enriched outputs | Yes | Unit tests cover both schema branches and parameter wiring.【F:tests/test_generator_assembler.py†L19-L76】 |
| External generator normalization & logging | Yes | Tests assert provenance, header redaction, retry taxonomy, and JSONL output.【F:tests/test_external_generator.py†L27-L345】 |
| CLI pipeline strict/relaxed flows | Yes (divergent behavior observed) | Integration tests show strict failure and relaxed success without MCP, highlighting the gap.【F:tests/test_pipeline.py†L45-L207】 |
| TCP default & resolver fallback | Yes | Resolver tests confirm TCP fallback for unset/invalid values.【F:tests/test_tcp.py†L175-L188】 |
| Socket failure detail | Yes | Critic test asserts `socket_unavailable` detail when path missing.【F:tests/test_critic.py†L188-L201】 |
| Header injection & size caps in live mode | Yes | Tests cover Authorization header, redaction, and request/response caps.【F:tests/test_external_generator.py†L130-L234】 |

# Dependencies and runtime
| Package | Used in | Required/Optional |
| --- | --- | --- |
| jsonschema | MCP validator shim and schema validation tests for assembler/external outputs.【F:labs/mcp/validate.py†L5-L78】【F:tests/test_generator_schema.py†L17-L26】 | Required |
| pytest | Test suite runner for unit/integration coverage.【F:requirements.txt†L2】【F:tests/test_external_generator.py†L8-L16】 | Required |

# Environment variables
- MCP transport defaults to TCP when `MCP_ENDPOINT` unset/invalid; TCP requires `MCP_HOST`/`MCP_PORT`, STDIO needs `MCP_ADAPTER_CMD`, and socket path is mandatory when selected.【F:labs/mcp_stdio.py†L162-L231】【F:.example.env†L1-L16】
- `LABS_SCHEMA_VERSION` sets generator default; CLI flag overrides per precedence docs/tests.【F:labs/agents/generator.py†L37-L52】【F:tests/test_pipeline.py†L300-L360】
- `LABS_FAIL_FAST` controls strict vs relaxed behavior across generator, critic, patches, and external generators.【F:labs/agents/generator.py†L19-L109】【F:labs/agents/critic.py†L22-L214】【F:labs/patches.py†L9-L158】
- External live calls use `LABS_EXTERNAL_LIVE`, provider API keys/endpoints/models/temperature, with `.example.env` documenting defaults and deprecated knobs (`SYN_SCHEMAS_DIR`).【F:labs/generator/external.py†L126-L179】【F:.example.env†L13-L29】

# Logging
- `log_jsonl` ensures JSONL formatting and directory creation; generator, critic, patches, and external modules call it with trace/strict/transport metadata.【F:labs/logging.py†L13-L35】【F:labs/agents/generator.py†L102-L199】【F:labs/agents/critic.py†L197-L250】【F:labs/patches.py†L33-L158】【F:labs/generator/external.py†L311-L372】
- Logs persist under `meta/output/labs/` (generator, critic, patches, external) with tests asserting entries for each artifact.【F:tests/test_pipeline.py†L120-L206】【F:tests/test_external_generator.py†L53-L192】【F:tests/test_patches.py†L11-L92】

# Documentation accuracy
- README documents TCP-default transport, socket optionality, schema-version targeting precedence, and external live setup consistent with spec.【F:README.md†L31-L111】
- `.example.env` mirrors documented defaults, including deprecated `SYN_SCHEMAS_DIR` noted for STDIO-only usage.【F:.example.env†L1-L29】
- Maintainer process doc references transport resolver expectations and schema-targeting discipline to avoid drift.【F:docs/process.md†L41-L52】

# Detected divergences
- Critic relaxed mode short-circuits MCP validation when the validator cannot be built, contrary to the “always invoke MCP” requirement, yet still returns `ok` and triggers persistence.【F:labs/agents/critic.py†L130-L188】【F:tests/test_pipeline.py†L197-L207】【F:docs/labs_spec.md†L29-L109】

# Recommendations
- Modify Critic/CLI relaxed flow to attempt MCP validation (with retries or explicit degraded flag) before accepting assets, and ensure assets are not persisted when validation was skipped.【F:labs/agents/critic.py†L130-L188】【F:labs/cli.py†L160-L189】
- Add regression tests covering the updated relaxed-mode behavior (e.g., assert MCP invoked and persistence blocked when validation unavailable) to protect spec compliance.【F:tests/test_pipeline.py†L197-L207】
