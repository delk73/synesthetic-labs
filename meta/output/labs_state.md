# Summary of repo state
- Generator/assembler branch between 0.7.3 legacy and 0.7.4+ enriched payloads, stamping `$schema`, pruning orphaned controls, and seeding provenance with tests over both schema families.【F:labs/generator/assembler.py†L67-L305】【F:tests/test_generator_assembler.py†L20-L76】
- MCP client stack defaults to TCP, exercises STDIO/socket fallbacks, and blocks persistence unless both `review.ok` and `mcp_response.ok` succeed, with strict/relaxed behaviours covered by tests.【F:labs/mcp_stdio.py†L162-L229】【F:labs/cli.py†L201-L240】【F:tests/test_pipeline.py†L102-L233】【F:tests/test_tcp.py†L175-L198】【F:tests/test_critic.py†L150-L218】
- External generators enforce env-driven live mode, headers, retry taxonomy, size caps, normalization, and provenance-rich logging, with schema validation exercised in unit tests.【F:labs/generator/external.py†L140-L827】【F:labs/logging.py†L13-L35】【F:tests/test_external_generator.py†L27-L384】【F:tests/test_generator_schema.py†L17-L33】

# Top gaps & fixes
- Replace the bespoke `_load_env_file` helper with `python-dotenv` and add the dependency so the CLI meets the mandated preload mechanism.【F:docs/labs_spec.md†L75-L79】【F:labs/cli.py†L13-L54】【F:requirements.txt†L1-L3】
- Remove `LABS_EXTERNAL_LIVE` usage/docs or clearly mark it deprecated per spec guidance to avoid contradictory live-mode toggles.【F:docs/labs_spec.md†L70-L114】【F:labs/cli.py†L51-L53】【F:.example.env†L19-L28】【F:README.md†L24-L170】
- Inject `"generationConfig":{"responseMimeType":"application/json"}` into Gemini live requests and add tests asserting structured output so the v0.3.4 requirement is satisfied.【F:docs/labs_spec.md†L82-L150】【F:labs/generator/external.py†L1203-L1248】【F:tests/test_external_generator.py†L27-L276】

# Alignment with labs_spec.md
| Spec item | Status | Evidence |
| --- | --- | --- |
| Schema targeting emits `$schema` and branches between 0.7.3 legacy and 0.7.4+ enriched payloads.【F:docs/labs_spec.md†L86-L101】 | Present | Assembler chooses legacy vs enriched builders and tests assert both payload shapes.【F:labs/generator/assembler.py†L122-L265】【F:tests/test_generator_assembler.py†L20-L76】 |
| MCP validation must run in strict/relaxed modes and block persistence when unavailable.【F:docs/labs_spec.md†L104-L114】 | Present | Critic surfaces outage taxonomy; CLI refuses to persist or return success when `mcp_response.ok` is falsy.【F:labs/agents/critic.py†L130-L215】【F:labs/cli.py†L201-L240】【F:tests/test_pipeline.py†L102-L233】 |
| CLI must preload `.env` via `python-dotenv` and warn on missing API keys.【F:docs/labs_spec.md†L70-L79】 | Divergent | CLI hand-parses `.env` and requirements omit `python-dotenv`, though warnings fire for missing keys.【F:labs/cli.py†L13-L54】【F:requirements.txt†L1-L3】 |
| TCP must be default transport with resolver fallback, STDIO/socket optional.【F:docs/labs_spec.md†L104-L114】 | Present | `resolve_mcp_endpoint` returns TCP on unset/invalid values with unit tests covering defaults and socket failures.【F:labs/mcp_stdio.py†L162-L229】【F:tests/test_tcp.py†L175-L198】【F:tests/test_critic.py†L188-L218】 |
| Gemini live calls must enforce structured JSON via `responseMimeType`.| Missing | Gemini `_build_request` omits the `responseMimeType` flag so structured output isn’t guaranteed.【F:docs/labs_spec.md†L82-L150】【F:labs/generator/external.py†L1203-L1248】 |
| External logs must capture provenance, schema_version, and `$schema`.【F:docs/labs_spec.md†L118-L133】 | Present | `record_run` writes schema metadata, provenance, and validation results to `external.jsonl` with tests asserting content.【F:labs/generator/external.py†L320-L356】【F:tests/test_external_generator.py†L53-L120】 |
| Deprecated env knobs (LABS_EXTERNAL_LIVE) must be removed or marked.| Divergent | Code and docs still rely on `LABS_EXTERNAL_LIVE` despite spec removal, creating drift.|【F:docs/labs_spec.md†L70-L114】【F:labs/cli.py†L51-L53】【F:.example.env†L19-L28】【F:README.md†L24-L170】 |

# Generator implementation
| Component | Status | Evidence |
| --- | --- | --- |
| Schema-aware assembly & `$schema` tagging | Present | `AssetAssembler` stamps schema URLs, constructs legacy/enriched payloads, and injects provenance.【F:labs/generator/assembler.py†L104-L265】 |
| Parameter index & control pruning | Present | Parameters aggregate from shader/tone/haptic, controls prune dangling mappings, and enriched assets carry sorted indices.【F:labs/generator/assembler.py†L83-L262】 |
| Experiment logging | Present | GeneratorAgent records schema_version, transport, strict flag, and validation summary before logging experiments.【F:labs/agents/generator.py†L67-L199】【F:tests/test_pipeline.py†L102-L188】 |

# Critic implementation
| Responsibility | Status | Evidence |
| --- | --- | --- |
| Outage taxonomy & strict fail-fast | Present | Critic maps MCP failures to `mcp_unavailable`/`mcp_error` and strict mode surfaces errors with tests validating paths.【F:labs/agents/critic.py†L130-L205】【F:tests/test_critic.py†L150-L218】 |
| Relaxed degradation without persistence | Present | Relaxed reviews warn, set `mcp_response.ok=False`, and CLI avoids persistence, matching pipeline tests.【F:labs/agents/critic.py†L154-L215】【F:labs/cli.py†L201-L240】【F:tests/test_pipeline.py†L197-L233】 |
| Review completeness (`mcp_response`, trace, strict/mode) | Present | Reviews always populate `mcp_response`, `transport`, `strict`, and `trace_id` before logging.【F:labs/agents/critic.py†L170-L215】【F:tests/test_pipeline.py†L197-L233】 |

# Assembler / Wiring step
- Parameter index deduplicated from shader/tone/haptic inputs and attached to enriched assets.【F:labs/generator/assembler.py†L83-L262】
- Control mappings prune unknown parameters before building control_parameters to avoid dangling references.【F:labs/generator/assembler.py†L83-L417】
- Provenance blocks capture generator/assembler metadata, timestamps, and rule bundle versions across schemas.【F:labs/generator/assembler.py†L95-L305】

# Patch lifecycle
- Preview/apply/rate commands log trace IDs, strict flags, modes, and transports while appending JSONL entries.【F:labs/patches.py†L47-L156】【F:tests/test_patches.py†L11-L92】
- Apply mode re-validates via CriticAgent and records failures with taxonomy-aligned payloads.【F:labs/patches.py†L71-L118】【F:tests/test_patches.py†L45-L92】

# MCP integration
- STDIO, TCP (default), and socket transports share `build_validator_from_env`, with resolver defaults enforced and tested.【F:labs/mcp_stdio.py†L162-L229】【F:tests/test_tcp.py†L175-L198】【F:tests/test_critic.py†L188-L218】
- CLI retries validator construction in relaxed mode, still invoking MCP and logging degraded warnings before critic review.【F:labs/cli.py†L101-L113】【F:tests/test_pipeline.py†L197-L233】
- Strict runs abort on MCP outages while relaxed runs return `ok:false` and halt persistence, satisfying spec gating.【F:labs/agents/critic.py†L130-L205】【F:labs/cli.py†L201-L240】
- Payload size limits (1 MiB responses) and TCP fallbacks align with validator contracts.【F:labs/mcp_stdio.py†L162-L229】【F:tests/test_tcp.py†L175-L198】

# External generator integration
- Gemini/OpenAI engines honour env-configured endpoints/keys, inject Authorization/X-Goog headers, redact logs, and obey retry taxonomy with tests for failure/no-retry cases.【F:labs/generator/external.py†L140-L538】【F:tests/test_external_generator.py†L90-L207】
- CLI flags surface engine selection, temperature, timeout, schema_version, and strictness, wiring external contexts into logging.【F:labs/cli.py†L124-L240】
- Normalization pipelines enforce allowed keys/types, merge defaults, and ensure MCP validation-ready payloads before return.【F:labs/generator/external.py†L640-L827】【F:tests/test_external_generator.py†L279-L384】
- MCP validation still runs post-generation; CLI/external logs store review results with schema metadata.【F:labs/generator/external.py†L320-L356】【F:tests/test_external_generator.py†L53-L120】

# External generation LIVE (v0.3.4)
- .env preload occurs at CLI import and warnings fire when API keys are missing, signalling mock fallback.【F:labs/cli.py†L47-L54】
- Live mode resolves endpoints/keys from env, performs connectivity checks, injects headers, and enforces 256KiB/1MiB caps with retry/backoff taxonomy.【F:labs/generator/external.py†L140-L538】【F:tests/test_external_generator.py†L180-L276】
- Logs redact secrets, capture trace/endpoint/schema_version, and persist into `meta/output/labs/external.jsonl`.【F:labs/generator/external.py†L320-L356】【F:labs/logging.py†L13-L35】
- Normalization applies before MCP validation, raising `bad_response`/`out_of_range` for violations with coverage in tests.【F:labs/generator/external.py†L640-L827】【F:tests/test_external_generator.py†L319-L384】
- Structured-output enforcement via `responseMimeType` remains unmet (see gaps above).【F:docs/labs_spec.md†L82-L150】【F:labs/generator/external.py†L1203-L1248】

# Test coverage
| Feature | Tested? | Evidence |
| --- | --- | --- |
| Schema 0.7.3 vs 0.7.4 generation | Yes | Unit tests validate both shapes and schema conformance.【F:tests/test_generator_assembler.py†L20-L76】【F:tests/test_generator_schema.py†L17-L33】 |
| MCP TCP default & resolver fallback | Yes | Tests assert TCP default on unset/invalid values.【F:tests/test_tcp.py†L175-L198】 |
| Socket failure taxonomy | Yes | Critic test checks `socket_unavailable` detail.【F:tests/test_critic.py†L188-L218】 |
| Relaxed mode degraded validation blocking persistence | Yes | CLI pipeline relaxed test ensures no persistence and warning status.【F:tests/test_pipeline.py†L197-L233】 |
| External header injection & redaction | Yes | Live header test asserts Authorization handling.【F:tests/test_external_generator.py†L115-L166】 |
| External size caps & retry taxonomy | Yes | Request/response cap and retry tests cover limits and no-retry taxonomy.【F:tests/test_external_generator.py†L166-L246】 |
| Gemini structured-output enforcement | No | No test asserts `responseMimeType`, mirroring missing implementation.【F:docs/labs_spec.md†L82-L150】【F:tests/test_external_generator.py†L27-L384】 |
| .env preload warnings via python-dotenv | No | CLI tests do not cover python-dotenv preload, and implementation is manual.【F:labs/cli.py†L13-L54】【F:tests/test_pipeline.py†L102-L233】 |

# Dependencies and runtime
| Package | Used in | Required/Optional |
| --- | --- | --- |
| jsonschema | Schema validation utility in MCP shim/tests for generator outputs.【F:requirements.txt†L1】【F:tests/test_generator_schema.py†L17-L33】 | Required |
| requests | Gemini connectivity check and HTTP fallbacks for external generators.【F:requirements.txt†L2】【F:labs/generator/external.py†L1145-L1182】 | Optional (live mode) |
| pytest | Test runner across unit/integration suites.【F:requirements.txt†L3】【F:tests/test_pipeline.py†L102-L233】 | Dev dependency |

# Environment variables
- `LABS_SCHEMA_VERSION` defaults to `0.7.3` and feeds generator/CLI schema targeting precedence (flag → env → default).【F:docs/labs_spec.md†L70-L86】【F:labs/cli.py†L132-L136】【F:labs/generator/assembler.py†L32-L47】
- `LABS_FAIL_FAST` controls strict vs relaxed paths for CLI, critic, patches, and external logging.【F:labs/cli.py†L101-L142】【F:labs/agents/critic.py†L20-L67】【F:labs/patches.py†L17-L152】
- MCP transport knobs (`MCP_ENDPOINT`, `MCP_HOST`, `MCP_PORT`, `MCP_ADAPTER_CMD`, `MCP_SOCKET_PATH`) resolve via TCP-default fallback with normalization safeguards.【F:labs/mcp_stdio.py†L162-L229】
- External engines draw credentials and endpoints from `GEMINI_API_KEY`/`GEMINI_ENDPOINT` and `OPENAI_API_KEY`/`OPENAI_ENDPOINT`, plus model overrides (`GEMINI_MODEL`, `OPENAI_MODEL`).【F:labs/generator/external.py†L1099-L1355】
- `LABS_EXTERNAL_LIVE` remains in code/docs despite spec removal and defaults to mock mode when unset, requiring cleanup.【F:.example.env†L19-L28】【F:labs/generator/external.py†L188-L214】
- `.env` preload occurs on CLI import but via manual parser; python-dotenv integration is absent.【F:labs/cli.py†L13-L54】

# Logging
- Generator, critic, patch, and external flows append JSONL records beneath `meta/output/labs/`, ensuring traceable experiments and validation context.【F:labs/agents/generator.py†L97-L199】【F:labs/agents/critic.py†L170-L215】【F:labs/patches.py†L47-L156】【F:labs/logging.py†L13-L35】
- External logs capture provenance, schema_version, `$schema`, request headers (redacted), raw response hash/size, and validation outcomes.【F:labs/generator/external.py†L320-L356】
- Failure paths populate `reason`/`detail` for MCP and external API issues, aligning with taxonomy expectations.【F:labs/agents/critic.py†L130-L205】【F:labs/generator/external.py†L200-L356】

# Documentation accuracy
- README documents TCP default, socket optionality, schema targeting precedence, and logging locations in line with implementation.【F:README.md†L64-L170】
- README and `.example.env` still reference `LABS_EXTERNAL_LIVE` and `load_dotenv`, conflicting with the spec’s removal of the knob and the manual loader implementation.【F:README.md†L24-L170】【F:.example.env†L19-L28】【F:labs/cli.py†L13-L54】
- Maintainer process doc highlights transport resolver discipline, schema targeting, and audit outputs, preventing drift.【F:docs/process.md†L33-L78】

# Detected divergences
- CLI environment preload deviates from the required `python-dotenv` usage, relying on a bespoke parser without the declared dependency.【F:docs/labs_spec.md†L75-L79】【F:labs/cli.py†L13-L54】【F:requirements.txt†L1-L3】
- `LABS_EXTERNAL_LIVE` persists across code and docs despite the spec removing deprecated env knobs, risking operator confusion.【F:docs/labs_spec.md†L70-L114】【F:labs/cli.py†L51-L53】【F:.example.env†L19-L28】【F:README.md†L24-L170】
- Gemini live requests omit the mandated `responseMimeType` flag, so structured JSON enforcement is missing.【F:docs/labs_spec.md†L82-L150】【F:labs/generator/external.py†L1203-L1248】

# Recommendations
- Integrate `python-dotenv` in the CLI startup (e.g., call `load_dotenv()`), add the package to dependencies, and adjust tests/docs accordingly to satisfy the preload requirement.【F:docs/labs_spec.md†L75-L79】【F:labs/cli.py†L13-L54】【F:requirements.txt†L1-L3】
- Excise or clearly deprecate `LABS_EXTERNAL_LIVE` usage across CLI, docs, and examples, replacing it with spec-approved live-mode toggles (e.g., presence of API keys).【F:docs/labs_spec.md†L70-L114】【F:labs/cli.py†L51-L53】【F:.example.env†L19-L28】【F:README.md†L24-L170】
- Update `GeminiGenerator._build_request` (and associated tests) to set `generationConfig.responseMimeType="application/json"`, asserting structured-output compliance in the test suite.【F:docs/labs_spec.md†L82-L150】【F:labs/generator/external.py†L1203-L1248】【F:tests/test_external_generator.py†L27-L276】
