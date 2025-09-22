## Summary of repo state
- Generator pipeline assembles shader/tone/haptic defaults, applies control/modulation pruning, and now emits deterministic IDs/timestamps when seeded (`labs/generator/assembler.py:44`; `labs/generator/assembler.py:100`).
- Critic enforces MCP validation unconditionally, flagging missing validators or adapter outages as failures (`labs/agents/critic.py:55`; `tests/test_critic.py:33`).
- CLI requires a working validator before persisting assets, exiting non-zero on any review failure and writing artefacts under `meta/output/labs/` (`labs/cli.py:111`; `labs/cli.py:165`).
- Logging and experiment outputs now target the spec hierarchy, with tests covering deterministic output and mandatory validation paths (`labs/agents/generator.py:12`; `tests/test_determinism.py:10`; `tests/test_pipeline.py:108`).

## Top gaps & fixes
- STDIO vs. TCP transport remains a divergence from the spec requirement; document or implement STDIO adapter parity (`docs/labs_spec.md:13`; `labs/cli.py:37`).
- `LABS_FAIL_FAST` no longer toggles behaviour, so relaxed mode is gone despite spec guidance; decide whether to restore configurable strictness or update docs/spec (`docs/labs_spec.md:52`; `labs/cli.py:179`).
- Modulation and rule bundle generators still ship ahead of scope but are now documented as an intentional divergence (`labs/generator/modulation.py:11`; `docs/labs_spec.md:82`).
- MCP availability is mandatory; consider adding integration coverage against a live adapter to guard future regressions (`labs/cli.py:157`; `tests/test_pipeline.py:108`).
- README and spec updated to reference `meta/prompts/init_labs.json`; ensure downstream tooling adopts the new artefact (`docs/labs_spec.md:20`; `meta/prompts/init_labs.json:1`).

## Alignment with labs_spec.md and init_labs.json
| Spec item | Status | Evidence |
| --- | --- | --- |
| Generator emits canonical shader/tone/haptic defaults | Present | `docs/labs_spec.md:11`; `labs/generator/shader.py:35`; `labs/generator/tone.py:33`; `labs/generator/haptic.py:33` |
| Controls map mouse axes to shader parameters | Present | `docs/labs_spec.md:43`; `labs/generator/control.py:12` |
| MCP validation via STDIO and required | Divergent | `docs/labs_spec.md:13`; `labs/cli.py:37`; `labs/agents/critic.py:55` |
| `LABS_FAIL_FAST` toggles strict failure semantics | Divergent | `docs/labs_spec.md:52`; `labs/cli.py:179`; `labs/experiments/prompt_experiment.py:91` |
| Logs stored under meta/output/labs/ | Present | `docs/labs_spec.md:14`; `labs/agents/generator.py:12`; `labs/cli.py:165` |
| Determinism test coverage | Present | `docs/labs_spec.md:64`; `tests/test_determinism.py:10` |
| Init artefact published as init_labs.json | Present | `docs/labs_spec.md:20`; `meta/prompts/init_labs.json:1` |

## Generator implementation
| Component | Status | Evidence |
| --- | --- | --- |
| `GeneratorAgent.propose` validates prompt and logs provenance | Present | `labs/agents/generator.py:30`; `tests/test_generator.py:10` |
| `GeneratorAgent.record_experiment` captures reviews with persisted paths | Present | `labs/agents/generator.py:71`; `tests/test_generator.py:27` |
| `AssetAssembler.generate` composes full asset with parameter index | Present | `labs/generator/assembler.py:44`; `labs/generator/assembler.py:95` |
| Seeded runs emit deterministic IDs/timestamps | Present | `labs/generator/assembler.py:50`; `tests/test_determinism.py:10` |
| Modulation and rule bundle generators included ahead of scope | Divergent | `labs/generator/modulation.py:11`; `docs/labs_spec.md:82` |

## Critic implementation
| Responsibility | Status | Evidence |
| --- | --- | --- |
| Required field checks for id/timestamp/prompt/provenance | Present | `labs/agents/critic.py:47` |
| Mandatory MCP validation (no skip) | Present | `labs/agents/critic.py:55`; `tests/test_critic.py:33` |
| Failures surface issues and block downstream persistence | Present | `labs/agents/critic.py:76`; `labs/cli.py:165` |
| Review logging captures MCP payloads | Present | `labs/agents/critic.py:94`; `tests/test_pipeline.py:24` |

## Assembler / Wiring step
- Parameter index collates shader/tone/haptic parameters for downstream use (`labs/generator/assembler.py:64`).
- Control mappings, modulators, and rule effects are pruned when targets are absent from the parameter index (`labs/generator/assembler.py:66`; `labs/generator/assembler.py:90`).
- Provenance records assembler agent, version, deterministic timestamp, and seed metadata on each asset (`labs/generator/assembler.py:75`).

## MCP integration
- Validation uses a TCP socket client that sends JSON payloads to the adapter (`labs/cli.py:37`).
- `_build_validator` now raises on misconfiguration, preventing silent skips when MCP details are missing (`labs/cli.py:111`; `tests/test_pipeline.py:58`).
- CLI commands exit non-zero when reviews fail, ensuring assets do not persist without MCP confirmation (`labs/cli.py:185`; `labs/cli.py:200`).

## Test coverage
| Feature | Tested? | Evidence |
| --- | --- | --- |
| Generator proposal logging | Yes | `tests/test_generator.py:10` |
| Critic hard-fail behaviour on MCP outages | Yes | `tests/test_critic.py:33` |
| CLI critique failure path | Yes | `tests/test_pipeline.py:53` |
| CLI generate persists validated asset | Yes | `tests/test_pipeline.py:108` |
| Deterministic asset output (fixed seed) | Yes | `tests/test_determinism.py:10` |
| Prompt experiment handles MCP validation | Yes | `tests/test_prompt_experiment.py:43` |

## Dependencies and runtime
| Package | Used in | Required/Optional |
| --- | --- | --- |
| `pytest>=7.0` | Test suite and CI (`requirements.txt:1`; `.github/workflows/ci.yml:18`) | Required for tests |

## Environment variables
- `LABS_FAIL_FAST` remains documented but is currently unused after enforcing mandatory MCP validation; CLI and experiments rely solely on review outcomes (`docs/labs_spec.md:52`; `labs/cli.py:185`).
- `MCP_HOST` (default `localhost`) auto-populates when missing during CLI runs (`labs/cli.py:111`; `tests/test_pipeline.py:60`).
- `MCP_PORT` (default `7000`) must parse as an integer; invalid values raise `MCPUnavailableError` (`labs/cli.py:115`; `labs/cli.py:123`).
- `SYN_SCHEMAS_DIR` (default `libs/synesthetic-schemas`) is injected for the CLI validator and required for startup (`labs/cli.py:118`; `labs/cli.py:127`).
- `LABS_EXPERIMENTS_DIR` overrides the persisted asset location for successful runs (`labs/cli.py:86`; `tests/test_pipeline.py:109`).
- `SYN_EXAMPLES_DIR` is exposed via Docker and `.env.example` but unused in code paths (`docker-compose.yml:10`; `.env.example:4`).

## Logging
- `log_jsonl` ensures directories exist and writes sorted JSON lines for consistency (`labs/logging.py:10`).
- Generator and critic agents log proposals, reviews, and experiments with provenance metadata (`labs/agents/generator.py:53`; `labs/agents/critic.py:89`).
- Persisted experiment assets land under `meta/output/labs/experiments/` when validation passes (`labs/cli.py:165`).

## Documentation accuracy
- README documents mandatory MCP validation and the `meta/output/labs/` logging layout (`README.md:24`; `README.md:33`).
- docs/labs_spec.md notes the `init_labs.json` artefact and the documented modulation/rule divergence (`docs/labs_spec.md:20`; `docs/labs_spec.md:82`).
- init prompt is available at both `init.json` and `init_labs.json` for backward compatibility (`meta/prompts/init.json:1`; `meta/prompts/init_labs.json:1`).

## Detected divergences
- MCP transport remains TCP-based rather than the specified STDIO channel (`labs/cli.py:37`; `docs/labs_spec.md:13`).
- Modulation and rule bundle components ship in v0.1 despite the spec deferring them (`labs/generator/modulation.py:11`; `docs/labs_spec.md:82`).

## Recommendations
- Implement STDIO-based MCP validation or update the spec to reflect the TCP adapter so transport expectations stay aligned (`labs/cli.py:37`; `docs/labs_spec.md:13`).
- Add integration coverage against a running MCP adapter to catch regressions in network/transport handling (`labs/cli.py:157`; `tests/test_pipeline.py:108`).
- Maintain both `init.json` and `init_labs.json` until upstream tooling switches, then deprecate the old name to reduce duplication (`meta/prompts/init.json:1`; `meta/prompts/init_labs.json:1`).
