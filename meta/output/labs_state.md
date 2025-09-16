## Summary of repo state
- Generator and critic agents implement prompt loading, proposal shaping, and critique logging with deterministic hooks (labs/agents/generator.py:33-92; labs/agents/critic.py:36-105).
- Pipeline helper coordinates generator → critic runs and emits JSONL traces under meta/output (labs/lifecycle/pipeline.py:17-55; labs/logging.py:6-15).
- CLI exposes generate/critique/pipeline commands but instantiates agents without MCP adapters, leading to skipped validation statuses by default (labs/cli.py:20-90; labs/agents/critic.py:82-85).
- Tests cover generator, critic, and pipeline flows with deterministic clocks and validators (tests/test_generator.py:11-53; tests/test_critic.py:9-53; tests/test_pipeline.py:12-70).
- Container harness remains minimal with Dockerfile + docker-compose executing pytest (Dockerfile:1-6; docker-compose.yml:1-7; test.sh:1-5).

## Top gaps & fixes (3–5 bullets)
- Missing MCP adapter wiring: CLI runs create CriticAgent without a validator so every review records "validation skipped"; add configuration or adapter loading to connect MCP validation in default flows (labs/cli.py:66-90; labs/agents/critic.py:82-85).
- No dependency or shim for synesthetic-schemas despite spec naming it as validation source of truth; introduce a lightweight validator module and pin the package so MCP-backed checks can execute (requirements.txt:1; labs/agents/critic.py:82-99).
- CLI behaviour is untested; add pytest coverage that exercises generate/critique/pipeline subcommands to lock argument parsing and logging (labs/cli.py:20-90; tests/test_generator.py:11-53).
- README omits pipeline usage and MCP requirements; extend documentation to describe pipeline command expectations and validator configuration (README.md:11-23; labs/cli.py:66-90).

## Alignment with labs_spec.md and init.json
| Spec item | Status | Evidence |
| --- | --- | --- |
| Generator agent assembles prompts with provenance and logging | Present | labs/agents/generator.py:33-92; tests/test_generator.py:11-53 |
| Critic agent performs sanity checks and defers to MCP validator hook | Present | labs/agents/critic.py:36-105; tests/test_critic.py:9-53 |
| Critic invokes MCP adapter by default in CLI pipeline | Divergent | labs/cli.py:66-90; labs/agents/critic.py:82-85 |
| Pipeline logs combined artefact to meta/output | Present | labs/lifecycle/pipeline.py:17-55; tests/test_pipeline.py:12-70 |
| Structured JSON logging stored under meta/output | Present | labs/logging.py:6-15; tests/test_generator.py:47-53 |
| Prompts stored under meta/prompts for reproducibility | Present | meta/prompts/init.json:1-34 |
| Consume synesthetic-schemas via MCP for validation | Missing | requirements.txt:1; labs/agents/critic.py:82-99 |
| Planned pytest coverage in tests/test_agents.py | Divergent | docs/labs_spec.md:32; tests/test_generator.py:11-53 |
| Backlog tracked for v0.2 features | Present | meta/backlog.md:1-9 |
| CLI documented with --help entry point | Present | labs/cli.py:20-62; README.md:11-21 |

## Test coverage
| Feature | Tested? | Evidence |
| --- | --- | --- |
| Generator proposal + logging | Yes | tests/test_generator.py:11-53 |
| Critic review + validator integration | Yes | tests/test_critic.py:9-53 |
| Pipeline end-to-end logging | Yes | tests/test_pipeline.py:12-70 |
| CLI command parsing/execution | No | tests/test_generator.py:11-53; tests/test_pipeline.py:12-70 |

## Dependencies and runtime
| Package | Used in | Required/Optional |
| --- | --- | --- |
| python 3.11 | Docker runtime base image | Required | Dockerfile:1-6 |
| pytest | Local + CI test execution | Required | requirements.txt:1; .github/workflows/ci.yml:17-20 |
| docker / docker-compose | Container harness via test.sh | Required | test.sh:1-5; docker-compose.yml:1-7 |

## Environment variables
- None defined; .env.example documents that v0.1 has no required values (.env.example:1).

## Documentation accuracy (README vs. labs_spec)
- README quickstart documents generator/critic commands in line with CLI expectations from the spec (README.md:11-23; docs/labs_spec.md:26-33).
- README logging section matches the spec mandate for structured JSONL traces in meta/output (README.md:34-35; docs/labs_spec.md:35-37).
- README omits the pipeline command and MCP adapter prerequisites highlighted by the spec's generator → critic workflow focus (README.md:11-23; docs/labs_spec.md:21-31).

## Detected divergences
- CLI pipeline creates a CriticAgent without an MCP validator, so default runs record skipped validation contrary to the MCP-backed validation requirement (labs/cli.py:66-90; labs/agents/critic.py:82-85).
- Spec references a consolidated tests/test_agents.py file while the repo maintains separate generator/critic/pipeline tests (docs/labs_spec.md:32; tests/test_generator.py:11-53).

## Recommendations
- Wire CriticAgent instances constructed by the CLI to a configurable MCP adapter so pipeline runs perform real validation instead of marking results as skipped (labs/cli.py:66-90; labs/agents/critic.py:82-99).
- Add a synesthetic-schemas-backed validator module and declare the dependency so MCP schema enforcement can execute in local and container runs (requirements.txt:1; labs/agents/critic.py:82-99).
- Introduce pytest coverage for CLI subcommands to safeguard argument parsing and JSON output (labs/cli.py:20-90; tests/test_generator.py:11-53).
- Update README to document pipeline usage and required MCP configuration so users understand how to achieve spec-compliant runs (README.md:11-23; docs/labs_spec.md:21-33).
