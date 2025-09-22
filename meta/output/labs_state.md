## Summary of repo state
- GeneratorAgent logs prompt provenance but leaves shader/tone/haptic assembly to AssetAssembler, so metadata-only proposals flow through non-CLI code paths (`labs/agents/generator.py:30`, `labs/generator/assembler.py:38`).
- MCP validation is mandatory: CLI subcommands bail out when `build_validator_from_env` fails, and CriticAgent records outages as errors (`labs/cli.py:78`, `labs/agents/critic.py:49`).
- Logging is centralized under `meta/output/labs/` via JSONL writers with provenance fields and persisted experiment artifacts (`labs/agents/generator.py:12`, `labs/logging.py:10`, `labs/cli.py:37`).

## Top gaps & fixes (3–5 bullets)
- GeneratorAgent currently returns metadata-only proposals, so non-CLI pipelines never see canonical shader/tone/haptic sections; wire `AssetAssembler.generate` into `GeneratorAgent.propose` and update call sites/tests to assert full assets (`labs/agents/generator.py:30`, `labs/cli.py:74`, `tests/test_pipeline.py:18`).
- Prompt experiment harness forwards these metadata-only proposals straight to MCP, which will fail once a real schema validator runs; assemble full assets before review and extend tests to confirm validation success (`labs/experiments/prompt_experiment.py:34`, `labs/agents/generator.py:30`, `tests/test_prompt_experiment.py:41`).
- `.env.example` omits the `MCP_HOST` and `MCP_PORT` variables called out in the init spec; document them alongside `MCP_ADAPTER_CMD` and plumb through validator startup docs (`.env.example:1`, `meta/prompts/init_labs.json:38`).
- Version markers advertise "v0.3/v0.2" across agents despite auditing the v0.1 release; align the version strings and documentation to the target milestone (`labs/agents/generator.py:25`, `labs/generator/assembler.py:24`, `README.md:3`).

## Alignment with labs_spec.md and init_labs.json
| Spec item | Status | Evidence |
| --- | --- | --- |
| Generator emits canonical sections with defaults | Divergent | docs/labs_spec.md:11, labs/agents/generator.py:30, labs/generator/assembler.py:38 |
| MCP validation over STDIO with fail-fast semantics | Present | docs/labs_spec.md:13, labs/mcp_stdio.py:84, labs/cli.py:78 |
| Logs stored under `meta/output/labs/` | Present | docs/labs_spec.md:14, labs/agents/generator.py:12, labs/agents/critic.py:12 |
| Initialization prompt published | Present | docs/labs_spec.md:20, meta/prompts/init_labs.json:1 |
| `.env.example` enumerates MCP host/port | Missing | meta/prompts/init_labs.json:38, .env.example:1 |

## Generator implementation
| Component | Status | Evidence |
| --- | --- | --- |
| GeneratorAgent.propose (asset construction) | Divergent | labs/agents/generator.py:30, labs/cli.py:74 |
| GeneratorAgent.record_experiment logging | Present | labs/agents/generator.py:71, tests/test_generator.py:27 |
| AssetAssembler.generate wiring | Present | labs/generator/assembler.py:38, labs/generator/assembler.py:62 |
| ShaderGenerator defaults | Present | labs/generator/shader.py:27, labs/generator/shader.py:96 |
| ToneGenerator defaults | Present | labs/generator/tone.py:8, labs/generator/tone.py:67 |
| HapticGenerator defaults | Present | labs/generator/haptic.py:8, labs/generator/haptic.py:47 |
| ControlGenerator mappings | Present | labs/generator/control.py:8, labs/generator/control.py:46 |
| MetaGenerator metadata | Present | labs/generator/meta.py:17, labs/generator/meta.py:20 |

## Critic implementation
| Responsibility | Status | Evidence |
| --- | --- | --- |
| Required field validation | Present | labs/agents/critic.py:21, tests/test_critic.py:23 |
| MCP validator construction & caching | Present | labs/agents/critic.py:49, labs/agents/critic.py:61 |
| Failure propagation for unavailable MCP | Present | labs/agents/critic.py:66, tests/test_critic.py:48 |
| Review logging with MCP payloads | Present | labs/agents/critic.py:82, tests/test_critic.py:34 |

## Assembler / Wiring step
- Parameter index aggregates shader, tone, and haptic input parameters for later reference pruning (`labs/generator/assembler.py:56`, `labs/generator/assembler.py:78`).
- Control mappings are deep-copied and filtered so only parameters present in the index survive (`labs/generator/assembler.py:58`, `labs/generator/assembler.py:108`).
- Provenance captures assembler agent/version, timestamp, and seed for deterministic replay (`labs/generator/assembler.py:62`, `labs/generator/assembler.py:71`).

## MCP integration
- CriticAgent lazily builds the STDIO validator and caches it per process, surfacing outages as review failures (`labs/agents/critic.py:49`, `labs/agents/critic.py:66`).
- CLI subcommands load the validator via `build_validator_from_env` and exit non-zero if the adapter cannot be launched (`labs/cli.py:74`, `labs/cli.py:110`).
- The STDIO bridge rejects missing commands, timeouts, and malformed payloads without local fallbacks, keeping validation strictly MCP-driven (`labs/mcp_stdio.py:84`, `labs/mcp_stdio.py:64`, `tests/test_critic.py:95`).

## Test coverage
| Feature | Tested? | Evidence |
| --- | --- | --- |
| Generator metadata logging | Yes | tests/test_generator.py:10 |
| AssetAssembler determinism | Yes | tests/test_determinism.py:10 |
| Generator→Critic pipeline with canonical asset | No | tests/test_pipeline.py:18, labs/agents/generator.py:30 |
| CLI generate persistence | Yes | tests/test_pipeline.py:58 |
| Prompt experiment harness with real MCP output | Partial | tests/test_prompt_experiment.py:15, labs/experiments/prompt_experiment.py:34 |

## Dependencies and runtime
| Package | Used in | Required/Optional |
| --- | --- | --- |
| pytest>=7.0 | CI and developer test runs (`requirements.txt:1`, `.github/workflows/ci.yml:15`) | Required |
| Python ≥3.11 | Runtime/version constraint from init prompt (`meta/prompts/init_labs.json:6`) | Required |

## Environment variables
- `MCP_ADAPTER_CMD` — required; absence triggers MCPUnavailableError in both CLI and Critic (`labs/mcp_stdio.py:87`, `labs/cli.py:78`, `tests/test_critic.py:95`).
- `SYN_SCHEMAS_DIR` — optional; forwarded to the subprocess environment when provided (`labs/mcp_stdio.py:93`).
- `LABS_EXPERIMENTS_DIR` — defaults to `meta/output/labs/experiments` when unset (`labs/cli.py:19`, `labs/cli.py:33`).
- `SYN_EXAMPLES_DIR` — listed in `.env.example` but unused by the runtime, indicating stale scaffolding (`.env.example:3`).
- Expected `MCP_HOST`/`MCP_PORT` entries from the init spec are missing, so operators cannot discover TCP-era variables even though they were requested (`meta/prompts/init_labs.json:38`, `.env.example:1`).

## Logging
- `log_jsonl` ensures directories exist and writes sorted JSON lines for downstream tooling (`labs/logging.py:10`).
- Generator and critic logs default to `meta/output/labs/generator.jsonl` and `meta/output/labs/critic.jsonl`, capturing provenance timestamps (`labs/agents/generator.py:12`, `labs/agents/generator.py:71`, `labs/agents/critic.py:12`).
- CLI persists validated assets to `meta/output/labs/experiments/` with relative paths recorded in generator experiment logs (`labs/cli.py:37`, `labs/cli.py:89`, `tests/test_pipeline.py:90`).
- Prompt experiment harness appends each run to an output JSONL for later analysis (`labs/experiments/prompt_experiment.py:52`).

## Documentation accuracy
- README instructs configuring `MCP_ADAPTER_CMD` with the bundled STDIO stub, matching the validation bridge implementation (`README.md:18`, `labs/mcp_stdio.py:84`).
- README states generator and critic logs live under `meta/output/labs/`, consistent with default log paths (`README.md:36`, `labs/agents/generator.py:12`, `labs/agents/critic.py:12`).
- README references `.env.example` for supported variables, but the file omits the MCP host/port entries described in the init spec (`README.md:30`, `.env.example:1`, `meta/prompts/init_labs.json:38`).

## Detected divergences
- GeneratorAgent remains a metadata logger and does not emit the canonical shader/tone/haptic bundle expected for v0.1 (`docs/labs_spec.md:11`, `labs/agents/generator.py:30`).
- Prompt experiment pipeline calls MCP with metadata-only payloads, diverging from the spec’s requirement to validate full assets (`labs/experiments/prompt_experiment.py:34`, `docs/labs_spec.md:63`).
- Version strings across generator components are set to v0.2/v0.3, diverging from the audited v0.1 release scope (`labs/agents/generator.py:25`, `labs/generator/assembler.py:24`).
- `.env.example` omits MCP host/port scaffolding requested by the initialization prompt (`meta/prompts/init_labs.json:38`, `.env.example:1`).

## Recommendations
- Refactor `GeneratorAgent.propose` to compose the canonical sections via `AssetAssembler` so every pipeline receives a schema-ready asset, and update generator/CLI tests to assert section presence (`labs/agents/generator.py:30`, `labs/generator/assembler.py:38`, `tests/test_pipeline.py:18`).
- Update `labs/experiments/prompt_experiment.py` to build full assets before review and extend its test to cover a real validator response instead of stubs (`labs/experiments/prompt_experiment.py:34`, `tests/test_prompt_experiment.py:15`).
- Extend `.env.example` and README to enumerate `MCP_HOST`/`MCP_PORT`, and ensure `build_validator_from_env` documents STDIO-only operation for clarity (`.env.example:1`, `README.md:30`, `meta/prompts/init_labs.json:38`).
- Normalize agent/version strings to v0.1 across generator and assembler components to match the audited release and avoid provenance confusion (`labs/agents/generator.py:25`, `labs/generator/assembler.py:24`, `labs/generator/shader.py:90`).
