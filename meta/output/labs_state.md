## Summary of repo state
- GeneratorAgent assembles canonical shader/tone/haptic/control/meta sections through AssetAssembler and records provenance-rich logs for every proposal (labs/agents/generator.py:37, labs/generator/assembler.py:38, tests/test_generator.py:24).
- CriticAgent enforces MCP validation, caching the STDIO validator and logging both successes and outages for traceability (labs/agents/critic.py:48, labs/agents/critic.py:66, tests/test_critic.py:34).
- CLI and prompt experiment harness orchestrate generation, MCP review, and artifact persistence under `meta/output/labs/` using the shared logging utilities (labs/cli.py:87, labs/experiments/prompt_experiment.py:52, labs/logging.py:10).

## Top gaps & fixes (3–5 bullets)
- Implement the documented `LABS_FAIL_FAST` toggle so CLI/critic flows can switch between strict and relaxed validation instead of always exiting on MCP outages (docs/labs_spec.md:50, labs/cli.py:77, labs/agents/critic.py:48).
- Update docs/labs_spec.md to reflect that CriticAgent is part of v0.1 now that the implementation and tests ship with the repo (docs/labs_spec.md:24, labs/agents/critic.py:15).
- Align MetaGenerator tags with the canonical `["circle","baseline"]` baseline or document the broadened taxonomy for this release (docs/labs_spec.md:38, labs/generator/meta.py:17).

## Alignment with labs_spec.md and init_labs.json
| Spec item | Status | Evidence |
| --- | --- | --- |
| Generator emits canonical sections with defaults | Present | docs/labs_spec.md:11, labs/agents/generator.py:37, tests/test_generator.py:24 |
| Assembler prunes dangling mappings | Present | docs/labs_spec.md:12, labs/generator/assembler.py:56, tests/test_generator_assembler.py:21 |
| MCP validation over STDIO | Present | docs/labs_spec.md:13, labs/mcp_stdio.py:84, labs/cli.py:77 |
| Logs stored under `meta/output/labs/` | Present | docs/labs_spec.md:14, labs/logging.py:10, labs/agents/generator.py:60 |
| CLI `generate` command available | Present | docs/labs_spec.md:15, labs/cli.py:65, tests/test_pipeline.py:62 |
| Initialization prompt published | Present | docs/labs_spec.md:20, meta/prompts/init_labs.json:1 |
| Fail-fast toggle via `LABS_FAIL_FAST` | Divergent | docs/labs_spec.md:50, labs/cli.py:77, labs/agents/critic.py:48 |
| Critic logs "validation skipped" on MCP outage | Divergent | meta/prompts/init_labs.json:21, labs/agents/critic.py:66 |
| `.env.example` enumerates MCP/SYN variables | Present | meta/prompts/init_labs.json:37, .env.example:1 |

## Generator implementation
| Component | Status | Evidence |
| --- | --- | --- |
| GeneratorAgent.propose (canonical asset) | Present | labs/agents/generator.py:37, tests/test_generator.py:24 |
| GeneratorAgent.record_experiment logging | Present | labs/agents/generator.py:64, tests/test_generator.py:40 |
| AssetAssembler.generate composition | Present | labs/generator/assembler.py:38, tests/test_generator_assembler.py:21 |
| ShaderGenerator defaults | Present | labs/generator/shader.py:70, tests/test_generator_components.py:53 |
| ToneGenerator defaults | Present | labs/generator/tone.py:63, tests/test_generator_components.py:59 |
| HapticGenerator defaults | Present | labs/generator/haptic.py:63, tests/test_generator_components.py:65 |
| ControlGenerator mappings | Divergent | labs/generator/control.py:8, docs/labs_spec.md:40 |
| MetaGenerator metadata | Divergent | labs/generator/meta.py:17, docs/labs_spec.md:38 |

## Critic implementation
| Responsibility | Status | Evidence |
| --- | --- | --- |
| Required field validation | Present | labs/agents/critic.py:41, tests/test_critic.py:23 |
| MCP validator construction & caching | Present | labs/agents/critic.py:48, labs/agents/critic.py:61 |
| Failure propagation for unavailable MCP | Present | labs/agents/critic.py:66, tests/test_critic.py:48 |
| Review logging with MCP payloads | Present | labs/agents/critic.py:82, tests/test_critic.py:34 |

## Assembler / Wiring step
- Parameter index aggregates shader, tone, and haptic inputs for pruning (`labs/generator/assembler.py:56`, `tests/test_generator_assembler.py:29`).
- Control mappings are deep-copied and filtered against the parameter index before inclusion (`labs/generator/assembler.py:58`, `labs/generator/assembler.py:108`).
- Provenance captures assembler agent, version, timestamp, and seed for replayability (`labs/generator/assembler.py:67`, `labs/generator/assembler.py:70`).

## MCP integration
- Both CLI and CriticAgent call the STDIO validator returned by `build_validator_from_env`, enforcing MCP authority on every review (labs/cli.py:77, labs/agents/critic.py:48).
- Outages raise `MCPUnavailableError`, surface in review issues, and flip exit codes so workflows fail fast (labs/mcp_stdio.py:64, labs/agents/critic.py:66, tests/test_pipeline.py:55).
- No relaxed mode is available; validation is always strict pending `LABS_FAIL_FAST` support (docs/labs_spec.md:50, labs/cli.py:77).

## Test coverage
| Feature | Tested? | Evidence |
| --- | --- | --- |
| Generator assembles canonical asset | Yes | tests/test_generator.py:24, tests/test_generator_components.py:53 |
| AssetAssembler determinism & pruning | Yes | tests/test_determinism.py:10, tests/test_generator_assembler.py:21 |
| Critic MCP failure propagation | Yes | tests/test_critic.py:48, tests/test_critic.py:79 |
| CLI generate persistence flow | Yes | tests/test_pipeline.py:62 |
| Prompt experiment end-to-end run | Yes | tests/test_prompt_experiment.py:12 |
| `LABS_FAIL_FAST` toggle behavior | No | docs/labs_spec.md:50, labs/cli.py:77 |

## Dependencies and runtime
| Package | Used in | Required/Optional |
| --- | --- | --- |
| pytest>=7.0 | Test suite execution (requirements.txt:1, .github/workflows/ci.yml:15) | Required |
| Python ≥3.11 | Runtime constraint from init prompt (meta/prompts/init_labs.json:6) | Required |

## Environment variables
- `MCP_ADAPTER_CMD` — required command for the STDIO validator; missing value raises `MCPUnavailableError` and halts reviews (labs/mcp_stdio.py:87, tests/test_critic.py:95).
- `SYN_SCHEMAS_DIR` — optional path forwarded to the MCP subprocess when provided (labs/mcp_stdio.py:93).
- `LABS_EXPERIMENTS_DIR` — overrides persisted asset directory; defaults to `meta/output/labs/experiments` (labs/cli.py:32, labs/cli.py:88).
- `MCP_HOST` / `MCP_PORT` — documented placeholders retained for compatibility but unused by the STDIO bridge (README.md:31, .env.example:4).

## Logging
- `log_jsonl` ensures directories exist and appends sorted JSON records for generator/critic logs (`labs/logging.py:10`, `labs/agents/generator.py:60`).
- Generator and critic default logs live under `meta/output/labs/` with provenance attached to both assets and review entries (`labs/agents/generator.py:12`, `labs/agents/critic.py:12`).
- Prompt experiments stream aggregated run data to JSON and JSONL files under the chosen output directory (`labs/experiments/prompt_experiment.py:61`, `labs/experiments/prompt_experiment.py:96`).

## Documentation accuracy
- README documents the STDIO-only MCP configuration, optional env vars, and log locations consistent with the implementation (README.md:24, labs/mcp_stdio.py:84, labs/cli.py:88).
- docs/labs_spec.md still classifies the critic as future work despite the shipped CriticAgent, creating confusion for v0.1 readers (docs/labs_spec.md:24, labs/agents/critic.py:15).
- docs/labs_spec.md canonical tags differ from the broader MetaGenerator taxonomy, warranting either metadata alignment or updated documentation (docs/labs_spec.md:38, labs/generator/meta.py:17).

## Detected divergences
- Fail-fast behavior is always strict; the `LABS_FAIL_FAST` toggle described in the spec is not implemented (docs/labs_spec.md:50, labs/cli.py:77).
- CriticAgent logs "MCP validation unavailable" rather than the specified "validation skipped" wording when MCP fails (meta/prompts/init_labs.json:21, labs/agents/critic.py:66).
- MetaGenerator tags extend beyond the canonical `["circle","baseline"]` baseline (docs/labs_spec.md:38, labs/generator/meta.py:17).
- ControlGenerator adds a tone detune mapping beyond the two canonical shader controls (docs/labs_spec.md:40, labs/generator/control.py:27).

## Recommendations
- Add `LABS_FAIL_FAST` environment handling with corresponding tests so operators can choose strict vs relaxed validation (docs/labs_spec.md:50, labs/cli.py:77, tests/test_pipeline.py:55).
- Refresh docs/labs_spec.md to acknowledge the CriticAgent workflow delivered in v0.1 (docs/labs_spec.md:24, labs/agents/critic.py:15).
- Decide whether to revert to the canonical meta tags/control set or update specs/tests to bless the expanded metadata (docs/labs_spec.md:38, labs/generator/meta.py:17, labs/generator/control.py:27).
