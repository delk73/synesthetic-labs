## Summary of repo state
- Generator pipeline assembles shader/tone/haptic plus extras via `AssetAssembler.generate` before critic review in the CLI flow (`labs/generator/assembler.py:37`; `labs/cli.py:165`).
- Critic enforces required keys and appends MCP responses but treats missing validators as benign unless fail-fast is enabled (`labs/agents/critic.py:25`; `labs/agents/critic.py:59`).
- Logging uses shared JSONL helpers yet writes to `meta/output/*.jsonl` instead of the spec-required `meta/output/labs/` hierarchy (`labs/logging.py:10`; `labs/agents/generator.py:12`; `docs/labs_spec.md:14`).
- Tests exercise logging, CLI persistence, and relaxed MCP skips but omit determinism and hard-fail outage scenarios (`tests/test_generator.py:10`; `tests/test_pipeline.py:33`; `docs/labs_spec.md:60`).

## Top gaps & fixes
- Enforce MCP validation as mandatory by making missing validators fail even in relaxed mode and bubbling errors through the CLI (`labs/agents/critic.py:59`; `labs/cli.py:170`).
- Restore spec logging layout by moving generator/critic JSONL sinks under `meta/output/labs/` and updating persistence paths accordingly (`labs/agents/generator.py:12`; `labs/agents/critic.py:12`; `labs/cli.py:20`).
- Align the init prompt artefact name with `init_labs.json` or document the `init.json` rename so automation can locate it (`meta/prompts/init.json:1`).
- Add deterministic asset assertions (fixed seed → stable payload) to cover the spec’s determinism requirement (`docs/labs_spec.md:60`; `tests/test_generator.py:10`).

## Alignment with labs_spec.md and init_labs.json
| Spec item | Status | Evidence |
| --- | --- | --- |
| Generator emits canonical shader/tone/haptic defaults | Present | `docs/labs_spec.md:11`; `labs/generator/shader.py:35`; `labs/generator/tone.py:33`; `labs/generator/haptic.py:33` |
| Controls map mouse axes to shader parameters | Present | `docs/labs_spec.md:42`; `labs/generator/control.py:12` |
| MCP validation via STDIO and required | Divergent | `docs/labs_spec.md:13`; `labs/cli.py:40`; `labs/agents/critic.py:59` |
| Logs stored under meta/output/labs/ | Divergent | `docs/labs_spec.md:14`; `labs/agents/generator.py:12`; `labs/agents/critic.py:12` |
| Determinism test coverage | Missing | `docs/labs_spec.md:60`; `tests/test_generator.py:10` |
| Init artefact published as init_labs.json | Divergent | `meta/prompts/init.json:1` |

## Generator implementation
| Component | Status | Evidence |
| --- | --- | --- |
| `GeneratorAgent.propose` validates prompt and logs provenance | Present | `labs/agents/generator.py:30`; `tests/test_generator.py:10` |
| `GeneratorAgent.record_experiment` captures reviews with persisted paths | Present | `labs/agents/generator.py:71`; `tests/test_generator.py:27` |
| `AssetAssembler.generate` composes full asset with parameter index | Present | `labs/generator/assembler.py:37`; `labs/generator/assembler.py:78` |
| Modulation and rule bundle generators included despite v0.1 deferral | Divergent | `labs/generator/modulation.py:11`; `labs/generator/rule_bundle.py:11`; `docs/labs_spec.md:45` |
| Generator logs write to meta/output root instead of meta/output/labs | Divergent | `labs/agents/generator.py:12`; `docs/labs_spec.md:55` |

## Critic implementation
| Responsibility | Status | Evidence |
| --- | --- | --- |
| Required field checks for id/timestamp/prompt/provenance | Present | `labs/agents/critic.py:49` |
| Mandatory MCP validation (no skip) | Divergent | `labs/agents/critic.py:59`; `labs/agents/critic.py:91` |
| Fail-fast converts outages into failures | Present | `labs/agents/critic.py:54`; `tests/test_critic.py:66` |
| Review logging captures MCP payloads | Present | `labs/agents/critic.py:94`; `tests/test_pipeline.py:24` |

## Assembler / Wiring step
- Parameter index collates shader/tone/haptic parameters for downstream use (`labs/generator/assembler.py:78`).
- Control mappings, modulators, and rule effects are pruned when their targets are missing from the parameter index (`labs/generator/assembler.py:85`; `labs/generator/assembler.py:104`).
- Provenance records assembler agent, version, and timestamp on each asset (`labs/generator/assembler.py:64`).

## MCP integration
- Validation uses a TCP socket client that sends JSON payloads (`labs/cli.py:37`).
- Missing validators log info/warning and allow skipped reviews when fail-fast is unset (`labs/agents/critic.py:59`; `labs/cli.py:204`).
- Fail-fast mode propagates MCPUnavailableError to CLI exit codes for `generate` and `critique` (`labs/cli.py:168`; `labs/cli.py:216`).

## Test coverage
| Feature | Tested? | Evidence |
| --- | --- | --- |
| Generator proposal logging | Yes | `tests/test_generator.py:10` |
| Critic skip vs fail-fast behavior | Yes | `tests/test_critic.py:37`; `tests/test_critic.py:66` |
| CLI critique persistence and MCP defaults | Yes | `tests/test_pipeline.py:33` |
| CLI generate persists validated asset | Yes | `tests/test_pipeline.py:108` |
| Deterministic asset output (fixed seed) | No | `docs/labs_spec.md:60`; `tests/test_generator.py:10` |
| MCP outage must fail when validator absent | No | `labs/agents/critic.py:59`; `tests/test_pipeline.py:33` |

## Dependencies and runtime
| Package | Used in | Required/Optional |
| --- | --- | --- |
| `pytest>=7.0` | Test suite and CI (`requirements.txt:1`; `.github/workflows/ci.yml:18`) | Required for tests |

## Environment variables
- `LABS_FAIL_FAST` (default unset) toggles relaxed vs failing reviews; defaults to relaxed skip-on-outage (`labs/agents/critic.py:54`; `labs/agents/critic.py:91`).
- `MCP_HOST` (default `localhost`) auto-populated when missing during CLI runs (`labs/cli.py:111`; `tests/test_pipeline.py:60`).
- `MCP_PORT` (default `7000`) coerces to int; invalid values skip validation unless fail-fast is active (`labs/cli.py:117`; `labs/cli.py:127`).
- `SYN_SCHEMAS_DIR` (default `libs/synesthetic-schemas`) is injected for the CLI validator but validation proceeds without checking the directory contents when unset (`labs/cli.py:122`; `labs/cli.py:136`).
- `LABS_EXPERIMENTS_DIR` overrides persisted asset location for successful runs (`labs/cli.py:86`; `tests/test_pipeline.py:108`).
- `SYN_EXAMPLES_DIR` is exposed via Docker and `.env.example` but unused in code paths (`docker-compose.yml:10`; `.env.example:4`).

## Logging
- `log_jsonl` ensures directories exist and writes sorted JSON lines for consistency (`labs/logging.py:10`).
- Generator and critic agents log proposals, reviews, and experiments with provenance metadata (`labs/agents/generator.py:47`; `labs/agents/critic.py:94`).
- Persisted experiment assets land under `meta/output/experiments/` when validation passes (`labs/cli.py:181`), diverging from the spec’s `meta/output/labs/` requirement (`docs/labs_spec.md:55`).

## Documentation accuracy
- README documents relaxed MCP skips while the spec requires mandatory validation, leaving readers with behaviour different from scope (`README.md:24`; `docs/labs_spec.md:13`).
- README omits the additional modulation/rule_bundle components that ship in v0.1 despite the spec deferring them (`README.md:19`; `labs/generator/modulation.py:11`; `docs/labs_spec.md:45`).
- Init artefact referenced in prompts exists as `init.json`, so external tooling expecting `init_labs.json` will not find it (`meta/prompts/init.json:1`).

## Detected divergences
- MCP validation is optional by default and uses TCP instead of the specified STDIO integration (`labs/cli.py:40`; `labs/agents/critic.py:59`; `docs/labs_spec.md:13`).
- Logging and persisted assets land in `meta/output/` top-level directories rather than the mandated `meta/output/labs/` (`labs/agents/generator.py:12`; `labs/cli.py:181`; `docs/labs_spec.md:14`).
- Generator bundle includes modulation and rule components tagged for v0.2+ scope (`labs/generator/modulation.py:11`; `labs/generator/rule_bundle.py:11`; `docs/labs_spec.md:45`).
- Init specification file is named `init.json`, diverging from the expected `init_labs.json` reference in prompts (`meta/prompts/init.json:1`).

## Recommendations
- Update critic and CLI flows to require MCP validation success (or explicit fail-fast opt-out) so skipped validations become failures in all modes, aligning with spec (`labs/agents/critic.py:59`; `labs/cli.py:204`).
- Relocate generator/critic logs and experiment outputs into `meta/output/labs/` and adjust README/tests to match the required directory structure (`labs/agents/generator.py:12`; `labs/agents/critic.py:12`; `labs/cli.py:181`).
- Either add `init_labs.json` alongside `init.json` or revise documentation/spec references to match the file name used in repo automation (`meta/prompts/init.json:1`; `meta/prompts/audit.json:5`).
- Add deterministic asset tests (e.g., fixed seed call to `AssetAssembler.generate`) verifying stable payloads and persisted artefacts (`docs/labs_spec.md:60`; `labs/generator/assembler.py:37`; `tests/test_generator.py:10`).
