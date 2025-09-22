# Agent Snapshot (v0.1 Audit)

## GeneratorAgent
- `propose` validates non-empty prompts, stamps UUID/ISO provenance, and appends proposals to the JSONL sink (`labs/agents/generator.py:30`; `tests/test_generator.py:10`).
- `record_experiment` links persisted asset paths and critic validation envelopes into the same log stream for replayability (`labs/agents/generator.py:71`; `tests/test_generator.py:27`).
- Default log target remains `meta/output/generator.jsonl`, diverging from the spec’s `meta/output/labs/` hierarchy (`labs/agents/generator.py:12`; `docs/labs_spec.md:14`).

## AssetAssembler
- Builds complete assets by cloning component generators and capturing provenance with timestamps and seed metadata (`labs/generator/assembler.py:37`; `labs/generator/assembler.py:64`).
- Collects a parameter index across shader/tone/haptic sections to prune invalid control, modulation, and rule references (`labs/generator/assembler.py:78`; `labs/generator/assembler.py:85`).
- Ships modulation and rule bundle components even though the v0.1 spec defers them to later releases (`labs/generator/modulation.py:11`; `docs/labs_spec.md:45`).

## CriticAgent
- Guards that assets include id/timestamp/prompt/provenance prior to validation and records outcomes with MCP payloads when available (`labs/agents/critic.py:49`; `labs/agents/critic.py:94`).
- Treats missing validators as informational skips unless `LABS_FAIL_FAST=1`, leaving MCP enforcement optional in default mode (`labs/agents/critic.py:54`; `labs/agents/critic.py:59`).

## SocketMCPValidator & CLI
- TCP validator sends JSON over sockets and converts I/O errors into `MCPUnavailableError` for higher-level handling (`labs/cli.py:37`; `labs/cli.py:50`).
- `_build_validator` auto-populates `MCP_HOST`, `MCP_PORT`, and `SYN_SCHEMAS_DIR`, enabling critiques without explicit configuration but bypassing the STDIO contract in the spec (`labs/cli.py:111`; `docs/labs_spec.md:13`).
- `generate` assembles assets, runs the critic, persists validated artefacts under `meta/output/experiments/`, and logs the run through `GeneratorAgent.record_experiment` (`labs/cli.py:165`; `labs/cli.py:181`).
- `critique` prints review payloads and only exits non-zero when fail-fast is active and the review failed, so skipped validations still succeed (`labs/cli.py:204`; `tests/test_pipeline.py:33`).

## Prompt Experiment Harness
- Loads prompt batches, reuses the shared validator builder, and logs each run to JSON/JSONL outputs for later analysis (`labs/experiments/prompt_experiment.py:25`; `labs/experiments/prompt_experiment.py:61`).
- Continues without MCP validation when outages occur in relaxed mode, logging a warning but treating runs as successes (`labs/experiments/prompt_experiment.py:29`; `labs/experiments/prompt_experiment.py:94`).

## Logging Utilities & Tests
- `log_jsonl` enforces directory creation and sorted JSON serialization so all agents share consistent logging semantics (`labs/logging.py:10`).
- Tests cover generator logging, critic fail-fast behaviour, CLI persistence, and prompt experiment outputs but lack determinism assertions and mandatory MCP outage failures (`tests/test_generator.py:10`; `tests/test_critic.py:66`; `tests/test_pipeline.py:108`; `docs/labs_spec.md:60`).
