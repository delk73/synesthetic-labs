## Summary of repo state
- Generator → critic pipeline remains the v0.1 STDIO flow with JSONL logging under `meta/output/labs/` (labs/agents/generator.py:25; labs/agents/critic.py:130).
- AssetAssembler emits shader/tone/haptic/control/meta only; modulation and rule bundle sections stay absent (labs/generator/assembler.py:62; tests/test_generator_assembler.py:35).
- Docs, container, and tests have not been uplifted for the v0.2 socket, patch, or rating requirements (README.md:1; Dockerfile:1; docs/labs_spec.md:70).

## Top gaps & fixes (3-5 bullets)
- Add the MCP Unix socket transport and validation path mandated in v0.2 (docs/labs_spec.md:72; labs/mcp_stdio.py:39).
- Implement patch lifecycle preview/apply/rate orchestration with persistence hooks (docs/labs_spec.md:73; labs/lifecycle/__init__.py:1).
- Extend Critic logging with ratings stubs per spec and cover with tests (docs/labs_spec.md:74; labs/agents/critic.py:118).
- Wire modulation and rule bundle stubs into the assembled asset and update assertions (docs/labs_spec.md:80; tests/test_generator_assembler.py:35).

## Alignment with labs_spec.md
| Spec item | Status | Evidence |
| --- | --- | --- |
| STDIO MCP validation | Present | `labs/mcp_stdio.py:39` sends assembled assets to the STDIO adapter and returns schema payloads. |
| Unix socket MCP transport | Missing | Spec requires socket mode (docs/labs_spec.md:72); runtime exposes only STDIO bridge (labs/mcp_stdio.py:1). |
| Patch lifecycle (preview/apply/rate) | Missing | Scope mandates lifecycle orchestration (docs/labs_spec.md:73); lifecycle package is a placeholder (labs/lifecycle/__init__.py:1). |
| Critic ratings stub logging | Missing | Spec calls for ratings stub (docs/labs_spec.md:74); review payload omits rating fields (labs/agents/critic.py:118). |
| Modulation stub in baseline | Missing | v0.2 baseline lists modulation (docs/labs_spec.md:80); assembler output lacks a modulation section (labs/generator/assembler.py:62). |
| Rule bundle stub in baseline | Missing | Spec adds rule bundle (docs/labs_spec.md:81); tests assert rule bundle is absent (tests/test_generator_assembler.py:35). |
| Path normalization / traversal guard | Missing | Validation requirements demand traversal rejection (docs/labs_spec.md:86); validator builder forwards paths without normalization (labs/mcp_stdio.py:84). |
| Container non-root hardening | Missing | Spec hardens container to non-root (docs/labs_spec.md:75); Dockerfile runs as root by default (Dockerfile:1). |
| Logging JSONL under meta/output | Present | `log_jsonl` writes sorted JSON lines and ensures directories (labs/logging.py:10). |
| Docs reflect socket + patch workflows | Divergent | README still documents v0.1 STDIO-only flow (README.md:1) despite v0.2 scope (docs/labs_spec.md:70). |

## Generator implementation
| Component | Status | Evidence |
| --- | --- | --- |
| ShaderGenerator | Present | Emits CircleSDF shader with uniforms and parameters (labs/generator/shader.py:45). |
| ToneGenerator | Present | Returns Tone.Synth configuration with envelope/effects (labs/generator/tone.py:34). |
| HapticGenerator | Present | Provides generic haptic profile and inputs (labs/generator/haptic.py:34). |
| ControlGenerator | Present | Supplies mouse mappings for shader parameters (labs/generator/control.py:19). |
| MetaGenerator | Present | Emits canonical metadata values (labs/generator/meta.py:17). |
| ModulationGenerator integration | Missing | Baseline omits modulation despite spec (docs/labs_spec.md:80; labs/generator/assembler.py:62). |
| RuleBundleGenerator integration | Missing | No rule bundle included in assembled assets (docs/labs_spec.md:81; tests/test_generator_assembler.py:35). |

## Critic implementation
| Responsibility | Status | Evidence |
| --- | --- | --- |
| Required field checks | Present | REQUIRED_KEYS guard enforces id/timestamp/prompt/provenance (labs/agents/critic.py:33). |
| Lazy MCP validator build | Present | Builds and caches validator on first review (labs/agents/critic.py:68). |
| Fail-fast vs relaxed toggle | Present | `LABS_FAIL_FAST` gate controls failure vs skip (labs/agents/critic.py:62). |
| Review logging with MCP payload | Present | Reviews append to `critic.jsonl` including MCP response (labs/agents/critic.py:130). |
| Ratings stub logging | Missing | Review payload lacks rating fields required in v0.2 (docs/labs_spec.md:74; labs/agents/critic.py:118). |
| Patch validation before apply | Missing | No hook to validate patched assets prior to apply (docs/labs_spec.md:87; labs/agents/critic.py:118). |

## Assembler / Wiring step
- Parameter index: `_collect_parameters` aggregates shader/tone/haptic inputs and stores `parameter_index` (labs/generator/assembler.py:56; labs/generator/assembler.py:78).
- Dangling reference pruning: `_prune_controls` filters mappings to known parameters (labs/generator/assembler.py:104).
- Provenance: Assets record assembler agent/version/timestamp/seed (labs/generator/assembler.py:67).

## Patch lifecycle
- Preview: Missing — lifecycle module is a stub with no preview entry points (labs/lifecycle/__init__.py:1).
- Apply: Missing — CLI only supports generate/critique commands (labs/cli.py:70).
- Rate stubs: Missing — Critic review lacks rating or score fields (labs/agents/critic.py:118).
- Logging: Missing — logs contain asset/review streams only, no patch journal (labs/logging.py:10; labs/agents/generator.py:98).

## MCP integration
- STDIO validation: Present via `StdioMCPValidator.validate` delegating to the adapter (labs/mcp_stdio.py:39).
- Socket validation: Missing — spec requires `MCP_ENDPOINT=socket` but no socket transport exists (docs/labs_spec.md:85; labs/mcp_stdio.py:1).
- Failure handling: Present — MCPUnavailableError surfaces with fail-fast semantics (labs/agents/critic.py:71).
- Strict vs relaxed mode: Present — `LABS_FAIL_FAST` toggles error vs skip (labs/agents/critic.py:62).

## Test coverage
| Feature | Tested? | Evidence |
| --- | --- | --- |
| Generator emits sections & logs | Yes | `test_generator_propose_writes_log` confirms sections and log entries (tests/test_generator.py:9). |
| Assembler parameter pruning | Yes | `test_asset_assembler_produces_consistent_payload` checks mappings vs parameters (tests/test_generator_assembler.py:21). |
| Critic fail-fast handling | Yes | `test_validation_failure_when_mcp_unavailable` exercises MCP outages (tests/test_critic.py:92). |
| CLI persistence flow | Yes | `test_cli_generate_persists_validated_asset` validates saved experiment assets (tests/test_pipeline.py:92). |
| Prompt experiment harness | Yes | Batch runner writes run + asset files (tests/test_prompt_experiment.py:12). |
| Socket transport | No | Spec expects socket round-trip tests (docs/labs_spec.md:96); suite covers STDIO only (tests/test_critic.py:92).
| Patch lifecycle integration | No | Lifecycle scope tests missing; lifecycle module is placeholder (docs/labs_spec.md:98; labs/lifecycle/__init__.py:1).
| Rating stub logging | No | Spec calls for rating log tests (docs/labs_spec.md:99); review payload has no rating field (labs/agents/critic.py:118).
| Path traversal rejection | No | Spec mandates traversal tests (docs/labs_spec.md:97); validator builder lacks normalization (labs/mcp_stdio.py:84).
| Container non-root enforcement | No | Spec requires non-root test (docs/labs_spec.md:100); Dockerfile runs as root (Dockerfile:1).

## Dependencies and runtime
| Package | Used in | Required/Optional |
| --- | --- | --- |
| pytest | Test suite runner invoked in CI (tests/**). | Required (requirements.txt:1). |
| python:3.11-slim | Docker base image for test container (Dockerfile:1). | Required. |

## Environment variables
- `MCP_ADAPTER_CMD`: Required; missing value raises `MCPUnavailableError` (labs/mcp_stdio.py:87). With fail-fast enabled the review fails when MCP is unreachable (labs/agents/critic.py:71).
- `SYN_SCHEMAS_DIR`: Optional; forwarded into the MCP adapter environment (labs/mcp_stdio.py:93). No special handling when MCP is unreachable.
- `LABS_EXPERIMENTS_DIR`: Default `meta/output/labs/experiments` controls persistence path (labs/cli.py:18).
- `LABS_FAIL_FAST`: Defaults to strict mode; `0` / `false` switches to relaxed logging when MCP is offline (labs/agents/critic.py:20; labs/agents/critic.py:79).
- `MCP_HOST`, `MCP_PORT`: Placeholder entries only in the sample env file with no runtime usage (.env.example:4).

## Logging
- Structured JSONL writes are handled by `log_jsonl`, ensuring directories exist and records are sorted (labs/logging.py:10).
- Generator logs asset proposals and experiment linkage to `meta/output/labs/generator.jsonl` (labs/agents/generator.py:12; labs/agents/generator.py:98).
- Critic logs reviews, MCP responses, and validation reasons to `meta/output/labs/critic.jsonl` (labs/agents/critic.py:13; labs/agents/critic.py:130).
- Patch/rating fields are absent from current logs; review payload has no rating data (labs/agents/critic.py:118).

## Documentation accuracy
- README still describes the v0.1 STDIO-only workflow and lacks socket or patch guidance (README.md:1; README.md:27) despite v0.2 scope requirements (docs/labs_spec.md:72).
- Generator spec claims the v0.2 baseline includes extra controls, modulations, and rule bundle that are not emitted by the assembler (docs/generator_spec.md:46; labs/generator/assembler.py:62).

## Detected divergences
- Test suite explicitly enforces absence of modulation and rule bundle components, diverging from the v0.2 baseline (tests/test_generator_assembler.py:35).
- `.env.example` retains unused MCP_HOST/MCP_PORT placeholders, reflecting earlier TCP plans rather than the mandated socket support (.env.example:4).
- Documentation remains anchored to v0.1 behavior, conflicting with the upgraded spec (README.md:1; docs/labs_spec.md:70).

## Recommendations
- Implement the MCP Unix socket transport (server/client handshake, size guard) and add coverage (docs/labs_spec.md:72; labs/mcp_stdio.py:1).
- Build patch preview/apply/rate orchestration with logging and CLI surfaces, backed by tests (docs/labs_spec.md:73; labs/cli.py:70).
- Extend CriticAgent and logs to capture rating stubs, plus unit/CLI coverage (docs/labs_spec.md:74; labs/agents/critic.py:118).
- Integrate modulation and rule bundle generators into AssetAssembler, revising assertions to expect them (docs/labs_spec.md:80; tests/test_generator_assembler.py:35).
- Harden the Docker image to run as a non-root user and normalize schema paths to block traversal (docs/labs_spec.md:75; Dockerfile:1; labs/mcp_stdio.py:84).
