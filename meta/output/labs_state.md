# Summary of repo state
- Generator and assembler default to schema version 0.7.3, branch between legacy and enriched payloads, and stamp `$schema` plus provenance while pruning dangling control mappings, with unit tests covering both schema families.【F:labs/generator/assembler.py†L67-L417】【F:tests/test_generator_assembler.py†L20-L76】
- External generators enforce env-configured live mode, retry/backoff taxonomy, request/response size caps, redacted headers, normalization, and schema-rich logging with coverage for success, failure, and retry scenarios.【F:labs/generator/external.py†L140-L538】【F:labs/generator/external.py†L600-L827】【F:tests/test_external_generator.py†L27-L279】
- Critic relaxed mode short-circuits MCP validation when the builder fails, returning `ok` with `mcp_response=None`; the CLI persists such assets, violating the spec’s “always validate and block persistence” rule.【F:labs/agents/critic.py†L130-L215】【F:labs/cli.py†L160-L199】【F:tests/test_pipeline.py†L197-L207】【F:docs/labs_spec.md†L113-L123】

# Top gaps & fixes
- Ensure relaxed-mode reviews still execute MCP validation (or explicitly mark failures) before setting `ok=True`, aligning with the mandate to always validate in both modes.【F:labs/agents/critic.py†L130-L205】【F:docs/labs_spec.md†L113-L120】
- Gate CLI persistence and success exit codes on confirmed MCP results (e.g., require a truthy `mcp_response` with `ok=True`) so assets aren’t saved when validation is skipped or fails.【F:labs/cli.py†L160-L199】【F:tests/test_pipeline.py†L197-L207】【F:docs/labs_spec.md†L121-L123】
- Populate `review["mcp_response"]` (even on degraded paths) and propagate the result into external logs so downstream tooling can audit validation status as required by the spec.【F:labs/agents/critic.py†L154-L215】【F:tests/test_critic.py†L162-L185】【F:labs/generator/external.py†L320-L356】【F:docs/labs_spec.md†L121-L146】

# Alignment with labs_spec.md
| Spec item | Status | Evidence |
| --- | --- | --- |
| Generator branches on schema version, emits `$schema`, and toggles legacy vs enriched fields per 0.7.3/0.7.4+ rules.【F:docs/labs_spec.md†L80-L99】 | Present | Assembler selects legacy vs enriched builds and tests assert both payload shapes.【F:labs/generator/assembler.py†L122-L265】【F:tests/test_generator_assembler.py†L20-L76】 |
| Pre-flight normalization rejects unknown keys, wrong types, and out-of-range values before MCP validation.【F:docs/labs_spec.md†L103-L109】 | Present | External normalization enforces key/type/bounds checks with dedicated tests for bad responses.【F:labs/generator/external.py†L680-L827】【F:tests/test_external_generator.py†L319-L384】 |
| MCP must run in strict and relaxed modes; failures should block persistence with `ok=False` and taxonomy details.【F:docs/labs_spec.md†L113-L123】 | Divergent | Relaxed reviews return `ok=True` with `mcp_response=None`, letting the CLI persist assets despite unavailable validation.【F:labs/agents/critic.py†L130-L205】【F:tests/test_pipeline.py†L197-L207】 |
| Reviews must always include an `mcp_response` block for logging and downstream auditing.【F:docs/labs_spec.md†L121-L123】 | Divergent | When validators cannot be built the critic leaves `mcp_response` unset, propagating `None` into CLI and external logs.【F:labs/agents/critic.py†L154-L215】【F:tests/test_critic.py†L162-L185】 |
| External logging must capture schema_version and `$schema` for each run.【F:docs/labs_spec.md†L127-L146】 | Present | `record_run` persists schema metadata and tests assert the JSONL payload content.【F:labs/generator/external.py†L320-L356】【F:tests/test_external_generator.py†L53-L90】 |

# Generator implementation
| Component | Status | Evidence |
| --- | --- | --- |
| Schema-aware assembler & branching | Present | `AssetAssembler` emits legacy vs enriched assets with `$schema`, parameter index, and provenance per schema target.【F:labs/generator/assembler.py†L67-L386】 |
| Parameter pruning & provenance seeding | Present | Control mappings are filtered to known parameters and provenance/meta defaults are injected before emission.【F:labs/generator/assembler.py†L83-L305】 |
| GeneratorAgent logging & experiment records | Present | Generator logs schema_version/transport and records experiments with validation status mirroring CLI precedence tests.【F:labs/agents/generator.py†L71-L199】【F:tests/test_pipeline.py†L102-L168】 |

# Critic implementation
| Responsibility | Status | Evidence |
| --- | --- | --- |
| Strict mode outage taxonomy | Present | Fail-fast path maps MCP errors to `mcp_unavailable`/`mcp_error` with log coverage and tests for TCP/STDIO/socket failures.【F:labs/agents/critic.py†L130-L188】【F:tests/test_critic.py†L188-L218】 |
| Relaxed mode still runs MCP & blocks persistence on failure | Divergent | Relaxed flow disables validation after builder errors yet returns `ok=True`, leading to persisted assets without MCP review.【F:labs/agents/critic.py†L130-L205】【F:tests/test_pipeline.py†L197-L207】 |
| Review metadata completeness (`mcp_response` always present) | Divergent | Reviews from degraded paths omit `mcp_response`, leaving `None` in logs contrary to the spec requirement.【F:labs/agents/critic.py†L197-L215】【F:tests/test_critic.py†L162-L185】【F:docs/labs_spec.md†L121-L123】 |

# Assembler / Wiring step
- Parameter index is aggregated from shader/tone/haptic sections, deduplicated, and attached to enriched payloads.【F:labs/generator/assembler.py†L83-L262】
- Control mappings are pruned to parameters in the index, preventing dangling references in control parameters.【F:labs/generator/assembler.py†L83-L417】
- Provenance blocks capture assembler/generator metadata and timestamps for both legacy and enriched assets.【F:labs/generator/assembler.py†L95-L305】

# Patch lifecycle
- `preview_patch` logs trace, mode, strict flag, and transport for dry runs with JSONL coverage in tests.【F:labs/patches.py†L47-L68】【F:tests/test_patches.py†L11-L29】
- `apply_patch` routes through the critic, records validation status/failure payloads, and emits transport metadata.【F:labs/patches.py†L71-L118】【F:tests/test_patches.py†L31-L63】
- `rate_patch` persists critic ratings with trace/transport fields alongside critic JSONL entries.【F:labs/patches.py†L121-L156】【F:tests/test_patches.py†L65-L92】

# MCP integration
- `resolve_mcp_endpoint` defaults to TCP when unset/invalid and `build_validator_from_env` provisions STDIO/socket/TCP adapters with required env checks and deprecation warnings.【F:labs/mcp_stdio.py†L162-L229】【F:tests/test_tcp.py†L175-L188】【F:tests/test_critic.py†L204-L218】
- TCP validator enforces payload caps via shared transport helpers, surfacing `MCPUnavailableError` on framing issues.【F:labs/mcp/tcp_client.py†L22-L74】【F:labs/transport.py†L8-L90】
- Critic/socket tests assert `socket_unavailable` taxonomy when `MCP_SOCKET_PATH` is missing, covering optional transport failure.【F:tests/test_critic.py†L188-L201】

# External generator integration
- Gemini/OpenAI classes honour env-configured live mode, build Authorization headers, redact logs, and attach provenance metadata.【F:labs/generator/external.py†L126-L488】
- Request/response size caps and retry taxonomy are enforced with dedicated tests for overflow, auth, and rate-limit scenarios.【F:labs/generator/external.py†L175-L538】【F:tests/test_external_generator.py†L200-L279】
- CLI flags for schema-version, seed, temperature, and timeout flow through to external generators with pipeline coverage.【F:labs/cli.py†L83-L143】【F:tests/test_pipeline.py†L300-L360】
- External runs append schema_version, `$schema`, provenance, and validation outcomes to `external.jsonl`, including failure detail on review errors.【F:labs/generator/external.py†L320-L356】【F:tests/test_external_generator.py†L53-L113】

# External generation LIVE (v0.3.4)
- Live mode toggles via `LABS_EXTERNAL_LIVE` and provider API key/endpoint env vars documented in `.example.env`.【F:labs/generator/external.py†L126-L204】【F:.example.env†L21-L29】
- Endpoint resolution requires configured URLs, injects Authorization headers, redacts secrets, and emits provenance including endpoint/mode.【F:labs/generator/external.py†L472-L538】【F:labs/generator/external.py†L1008-L1046】
- Timeout/backoff logic applies capped exponential delay with retry taxonomy distinguishing auth, rate-limit, and server errors.【F:labs/generator/external.py†L453-L538】【F:tests/test_external_generator.py†L236-L279】
- Normalization pipelines map provider payloads to schema-valid assets (legacy vs enriched) before MCP validation.【F:labs/generator/external.py†L600-L678】【F:tests/test_external_generator.py†L27-L192】

# Test coverage
| Feature | Tested? | Evidence |
| --- | --- | --- |
| Assembler legacy/enriched outputs | Yes | Unit tests assert 0.7.3 vs 0.7.4 payload differences and provenance wiring.【F:tests/test_generator_assembler.py†L20-L76】 |
| Schema validation against 0.7.4 | Yes | JSON Schema tests validate internal/external assets against the bundled corpus.【F:tests/test_generator_schema.py†L20-L33】 |
| CLI strict vs relaxed flows | Yes (divergent outcome documented) | Pipeline tests cover strict success and relaxed persistence despite MCP outages.【F:tests/test_pipeline.py†L102-L207】 |
| Resolver fallback & TCP transport | Yes | Tests assert TCP default when endpoint unset/invalid and live TCP validation path.【F:tests/test_tcp.py†L162-L188】 |
| Socket failure taxonomy | Yes | Critic test expects `socket_unavailable` detail when socket path missing.【F:tests/test_critic.py†L188-L201】 |
| External header injection & redaction | Yes | Live-mode test inspects Authorization header/redaction and endpoint propagation.【F:tests/test_external_generator.py†L130-L192】 |
| External size caps & retry taxonomy | Yes | Tests cover 256KiB/1MiB caps, auth errors, and rate-limit retries.【F:tests/test_external_generator.py†L200-L279】 |

# Dependencies and runtime
| Package | Used in | Required/Optional |
| --- | --- | --- |
| jsonschema | Schema validation utility in MCP shim and schema tests.【F:requirements.txt†L1】【F:tests/test_generator_schema.py†L20-L33】 | Required |
| pytest | Test runner for unit/integration suites across modules.【F:requirements.txt†L2】【F:tests/test_external_generator.py†L8-L24】 | Required |

# Environment variables
- MCP transport defaults to TCP with host/port overrides; STDIO/socket require adapter commands or socket paths, with deprecated `SYN_SCHEMAS_DIR` noted for STDIO only.【F:labs/mcp_stdio.py†L162-L229】【F:.example.env†L1-L16】
- `LABS_SCHEMA_VERSION` sets the generator default while CLI flags take precedence, matching maintainer guidance and tests.【F:labs/agents/generator.py†L37-L108】【F:tests/test_pipeline.py†L300-L360】【F:docs/process.md†L47-L52】
- `LABS_FAIL_FAST` controls strict vs relaxed flows across generator, critic, patches, and external generators.【F:labs/agents/generator.py†L19-L109】【F:labs/agents/critic.py†L22-L215】【F:labs/patches.py†L17-L156】
- External live calls rely on `LABS_EXTERNAL_LIVE`, provider API keys/endpoints/models documented in `.example.env`.【F:labs/generator/external.py†L126-L204】【F:.example.env†L21-L29】

# Logging
- `log_jsonl` and `log_external_generation` guarantee JSONL emission with timestamps, used by generator, critic, patches, and external modules.【F:labs/logging.py†L13-L35】【F:labs/agents/generator.py†L102-L199】【F:labs/agents/critic.py†L197-L215】【F:labs/patches.py†L47-L156】【F:labs/generator/external.py†L320-L356】
- Tests assert generator/critic/pipeline/external JSONL outputs, ensuring logs land under `meta/output/labs/`.【F:tests/test_pipeline.py†L102-L168】【F:tests/test_external_generator.py†L53-L192】【F:tests/test_patches.py†L11-L92】【F:tests/test_logging.py†L10-L20】

# Documentation accuracy
- README documents TCP default, socket optionality, schema-version targeting precedence, and external live setup consistent with the spec.【F:README.md†L31-L111】
- `.example.env` mirrors transport defaults, schema targeting, live-mode env keys, and marks `SYN_SCHEMAS_DIR` deprecated.【F:.example.env†L1-L29】
- Maintainer process references the transport resolver and schema targeting discipline to avoid drift.【F:docs/process.md†L41-L52】

# Detected divergences
- Relaxed critic path skips MCP validation yet returns `ok=True`, leading to persisted assets contrary to spec requirements.【F:labs/agents/critic.py†L130-L205】【F:tests/test_pipeline.py†L197-L207】【F:docs/labs_spec.md†L113-L123】
- Reviews from degraded runs omit the `mcp_response` block, so CLI/external logs lack mandated validation metadata.【F:labs/agents/critic.py†L197-L215】【F:tests/test_critic.py†L162-L185】【F:docs/labs_spec.md†L121-L123】

# Recommendations
- Restore relaxed-mode validation (or mark reviews `ok=False`) and propagate explicit `mcp_unavailable` failures to satisfy the “always validate” contract.【F:labs/agents/critic.py†L130-L205】【F:docs/labs_spec.md†L113-L120】
- Require a populated `mcp_response` with `ok=True` before persisting assets or reporting success, preventing unvalidated experiments from being stored.【F:labs/cli.py†L160-L199】【F:docs/labs_spec.md†L121-L123】
- Backfill tests covering degraded-mode validation/persistence to guard against regressions once the critic and CLI changes land.【F:tests/test_pipeline.py†L197-L207】
