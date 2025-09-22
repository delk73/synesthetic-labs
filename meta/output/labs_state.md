## Summary of repo state
- Generator pipeline assembles shader/tone/haptic defaults, prunes control mappings, and emits deterministic IDs/timestamps when seeded (`labs/generator/assembler.py:44`; `labs/generator/assembler.py:100`).
- Critic fetches a STDIO MCP validator on demand and blocks execution whenever the adapter command fails, logging structured review payloads under `meta/output/labs/` (`labs/agents/critic.py:55`; `tests/test_critic.py:63`).
- CLI invokes the STDIO bridge via `MCP_ADAPTER_CMD`, persists validated assets under `meta/output/labs/experiments/`, and returns non-zero whenever reviews fail (`labs/cli.py:36`; `labs/cli.py:74`; `tests/test_pipeline.py:62`).
- Modulation and rule bundle generators live under `labs/experimental/` and are no longer part of the v0.1 asset assembly flow (`labs/generator/assembler.py:75`; `labs/experimental/__init__.py:3`).

## Top gaps & fixes
- Extend integration coverage against a real MCP adapter to exercise the STDIO bridge end-to-end (`labs/mcp_stdio.py:26`; `tests/test_pipeline.py:62`).
- Consider reintroducing a relaxed mode toggle or update docs if strict validation is the only supported behaviour (`docs/labs_spec.md:52`; `labs/cli.py:185`).

## Alignment with labs_spec.md and init_labs.json
| Spec item | Status | Evidence |
| --- | --- | --- |
| Generator emits canonical shader/tone/haptic defaults | Present | `docs/labs_spec.md:11`; `labs/generator/shader.py:35`; `labs/generator/tone.py:33`; `labs/generator/haptic.py:33` |
| Controls map mouse axes to shader parameters | Present | `docs/labs_spec.md:43`; `labs/generator/control.py:12` |
| MCP validation via STDIO and required | Present | `docs/labs_spec.md:48`; `labs/cli.py:36`; `labs/mcp_stdio.py:87` |
| Logs stored under meta/output/labs/ | Present | `docs/labs_spec.md:14`; `labs/agents/generator.py:12`; `labs/cli.py:74` |
| Determinism test coverage | Present | `docs/labs_spec.md:64`; `tests/test_determinism.py:10` |
| Init artefact published as init_labs.json | Present | `docs/labs_spec.md:20`; `meta/prompts/init_labs.json:1` |

## Generator implementation
| Component | Status | Evidence |
| --- | --- | --- |
| `GeneratorAgent.propose` validates prompt and logs provenance | Present | `labs/agents/generator.py:30`; `tests/test_generator.py:10` |
| `GeneratorAgent.record_experiment` captures reviews with persisted paths | Present | `labs/agents/generator.py:71`; `tests/test_generator.py:27` |
| `AssetAssembler.generate` composes full asset with parameter index | Present | `labs/generator/assembler.py:44`; `labs/generator/assembler.py:95` |
| Seeded runs emit deterministic IDs/timestamps | Present | `labs/generator/assembler.py:50`; `tests/test_determinism.py:10` |
| Modulation and rule bundle generators relocated to experimental package | Present | `labs/generator/assembler.py:75`; `labs/experimental/__init__.py:3` |

## Critic implementation
| Responsibility | Status | Evidence |
| --- | --- | --- |
| Required field checks for id/timestamp/prompt/provenance | Present | `labs/agents/critic.py:47` |
| Mandatory MCP validation (no skip) | Present | `labs/agents/critic.py:55`; `tests/test_critic.py:63` |
| Failures surface issues and block downstream persistence | Present | `labs/agents/critic.py:77`; `labs/cli.py:101` |
| Review logging captures MCP payloads | Present | `labs/agents/critic.py:94`; `tests/test_pipeline.py:94` |

## Assembler / Wiring step
- Parameter index collates shader/tone/haptic parameters for downstream use (`labs/generator/assembler.py:64`).
- Control mappings referencing unknown parameters are pruned before persistence (`labs/generator/assembler.py:66`).
- Provenance records assembler agent, version, deterministic timestamp, and seed metadata on each asset (`labs/generator/assembler.py:75`).

## MCP integration
- STDIO bridge spawns the adapter via `subprocess.Popen`, streams JSON over stdin/stdout, and raises on timeouts or malformed payloads (`labs/mcp_stdio.py:30`; `labs/mcp_stdio.py:58`).
- CLI stops immediately when the adapter command is absent or fails, preventing unvalidated assets from persisting (`labs/cli.py:69`; `tests/test_pipeline.py:49`).
- Prompt experiments reuse the same builder and return non-zero on any failed review (`labs/experiments/prompt_experiment.py:25`; `labs/experiments/prompt_experiment.py:87`).

## Test coverage
| Feature | Tested? | Evidence |
| --- | --- | --- |
| Generator proposal logging | Yes | `tests/test_generator.py:10` |
| Critic handling of missing STDIO adapter | Yes | `tests/test_critic.py:70` |
| CLI critique failure path | Yes | `tests/test_pipeline.py:49` |
| CLI generate persists validated asset | Yes | `tests/test_pipeline.py:78` |
| Deterministic asset output (fixed seed) | Yes | `tests/test_determinism.py:10` |
| Prompt experiment requires MCP validation | Yes | `tests/test_prompt_experiment.py:43` |

## Dependencies and runtime
| Package | Used in | Required/Optional |
| --- | --- | --- |
| `pytest>=7.0` | Test suite and CI (`requirements.txt:1`; `.github/workflows/ci.yml:18`) | Required for tests |

## Environment variables
- `MCP_ADAPTER_CMD` defines the STDIO adapter command and must be set for CLI and experiments to run (`labs/mcp_stdio.py:74`; `README.md:24`).
- `SYN_SCHEMAS_DIR` forwards schema paths to the adapter when provided (`labs/mcp_stdio.py:78`; `docker-compose.yml:6`).
- `LABS_EXPERIMENTS_DIR` overrides the persisted asset location for successful runs (`labs/cli.py:43`; `tests/test_pipeline.py:69`).
- `SYN_EXAMPLES_DIR` is exposed via Docker and `.env.example` but unused in code paths (`docker-compose.yml:6`; `.env.example:3`).

## Logging
- `log_jsonl` ensures directories exist and writes sorted JSON lines for consistency (`labs/logging.py:10`).
- Generator and critic agents log proposals, reviews, and experiments with provenance metadata (`labs/agents/generator.py:53`; `labs/agents/critic.py:89`).
- Persisted experiment assets land under `meta/output/labs/experiments/` when validation passes (`labs/cli.py:88`).

## Documentation accuracy
- README documents mandatory STDIO validation, environment variables, and logging layout (`README.md:24`; `README.md:31`).
- docs/labs_spec.md reflects the STDIO transport, deferred modulation/rule generators, and init prompt location (`docs/labs_spec.md:13`; `docs/labs_spec.md:46`; `docs/labs_spec.md:20`).
- init prompt is available at both `init.json` and `init_labs.json` for compatibility (`meta/prompts/init.json:1`; `meta/prompts/init_labs.json:1`).

## Detected divergences
- None observed.

## Recommendations
- Add a thin integration test harness that exercises the STDIO bridge against a real adapter implementation (`labs/mcp_stdio.py:30`; `tests/test_pipeline.py:49`).
- Evaluate whether a configurable relaxed mode is required or if full fail-fast semantics can be codified in docs/spec (`docs/labs_spec.md:52`; `labs/cli.py:185`).
