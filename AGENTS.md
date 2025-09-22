# Agent Snapshot (v0.1 Audit)

## GeneratorAgent
- `propose` validates non-empty prompts, stamps UUID/ISO provenance, and appends proposals to the JSONL sink (`labs/agents/generator.py:30`; `tests/test_generator.py:10`).
- `record_experiment` links persisted asset paths and critic validation envelopes into the same log stream for replayability (`labs/agents/generator.py:71`; `tests/test_generator.py:27`).
- Default log target now lives under `meta/output/labs/generator.jsonl`, matching the spec hierarchy (`labs/agents/generator.py:12`; `docs/labs_spec.md:14`).

## AssetAssembler
- Builds complete assets by cloning component generators and capturing provenance with timestamps and seed metadata (`labs/generator/assembler.py:44`; `labs/generator/assembler.py:75`).
- Collects a parameter index across shader/tone/haptic sections to prune invalid control, modulation, and rule references (`labs/generator/assembler.py:64`; `labs/generator/assembler.py:95`).
- Derives deterministic UUID/timestamp pairs whenever a seed is provided, yielding byte-identical payloads in repeated runs (`labs/generator/assembler.py:50`; `tests/test_determinism.py:10`).
- Ships modulation and rule bundle components early, a documented divergence retained for richer wiring coverage (`labs/generator/modulation.py:11`; `docs/labs_spec.md:82`).

## CriticAgent
- Guards that assets include id/timestamp/prompt/provenance prior to validation and records outcomes with MCP payloads when available (`labs/agents/critic.py:47`; `labs/agents/critic.py:94`).
- Missing validators or MCP outages now yield hard failures, preventing downstream flows from proceeding without schema confirmation (`labs/agents/critic.py:55`; `tests/test_critic.py:33`).

## SocketMCPValidator & CLI
- TCP validator sends JSON over sockets and converts I/O errors into `MCPUnavailableError` for higher-level handling (`labs/cli.py:37`; `labs/cli.py:50`).
- `_build_validator` auto-populates `MCP_HOST`, `MCP_PORT`, and `SYN_SCHEMAS_DIR`, and now raises on misconfiguration so CLI and experiments cannot skip validation (`labs/cli.py:111`; `tests/test_pipeline.py:58`).
- `generate` assembles assets, runs the critic, persists validated artefacts under `meta/output/labs/experiments/`, and logs the run through `GeneratorAgent.record_experiment` (`labs/cli.py:153`; `labs/cli.py:165`).
- `critique` prints review payloads and exits non-zero whenever MCP validation fails, regardless of `LABS_FAIL_FAST` (`labs/cli.py:188`; `tests/test_pipeline.py:53`).

## Prompt Experiment Harness
- Loads prompt batches, reuses the shared validator builder, and logs each run to JSON/JSONL outputs for later analysis (`labs/experiments/prompt_experiment.py:32`; `labs/experiments/prompt_experiment.py:58`).
- Requires a working MCP validator; outages propagate as failures rather than silent skips (`labs/experiments/prompt_experiment.py:25`; `tests/test_prompt_experiment.py:41`).

## Logging Utilities & Tests
- `log_jsonl` enforces directory creation and sorted JSON serialization so all agents share consistent logging semantics (`labs/logging.py:10`).
- Test suite now covers deterministic seeded output, mandatory MCP failures, and the updated logging layout (`tests/test_determinism.py:10`; `tests/test_critic.py:33`; `tests/test_pipeline.py:108`).
