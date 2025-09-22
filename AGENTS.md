# Agent Snapshot (v0.1 Audit)

## GeneratorAgent
- `propose` validates non-empty prompts, stamps UUID/ISO provenance, and appends proposals to the JSONL sink (`labs/agents/generator.py:30`; `tests/test_generator.py:10`).
- `record_experiment` links persisted asset paths and critic validation envelopes into the same log stream for replayability (`labs/agents/generator.py:71`; `tests/test_generator.py:27`).
- Default log target now lives under `meta/output/labs/generator.jsonl`, matching the spec hierarchy (`labs/agents/generator.py:12`; `docs/labs_spec.md:14`).

## AssetAssembler
- Builds complete assets by cloning component generators and capturing provenance with timestamps and seed metadata (`labs/generator/assembler.py:44`; `labs/generator/assembler.py:75`).
- Collects a parameter index across shader/tone/haptic sections to prune invalid control references (`labs/generator/assembler.py:64`).
- Derives deterministic UUID/timestamp pairs whenever a seed is provided, yielding byte-identical payloads in repeated runs (`labs/generator/assembler.py:50`; `tests/test_determinism.py:10`).
- Modulation and rule bundle generators live under `labs.experimental` for v0.2+ previews (`labs/experimental/__init__.py:7`).

## CriticAgent
- Guards that assets include id/timestamp/prompt/provenance prior to validation and records outcomes with MCP payloads when available (`labs/agents/critic.py:47`; `labs/agents/critic.py:94`).
- Missing validators or MCP outages now yield hard failures, preventing downstream flows from proceeding without schema confirmation (`labs/agents/critic.py:55`; `tests/test_critic.py:33`).

## STDIO MCP Validator & CLI
- `build_validator_from_env` constructs a STDIO bridge using `MCP_ADAPTER_CMD`, spawning the adapter with `subprocess.Popen` and raising on timeouts or malformed payloads (`labs/mcp_stdio.py:30`; `labs/mcp_stdio.py:74`).
- CLI commands fail fast when the adapter command is missing or errors, logging the outage and exiting non-zero (`labs/cli.py:78`; `tests/test_pipeline.py:49`).
- Successful runs persist validated artefacts under `meta/output/labs/experiments/` and emit experiment logs linking reviews to file paths (`labs/cli.py:87`; `labs/cli.py:104`).
- `CriticAgent` caches the validator callback and surfaces STDIO failures as review issues while recording MCP responses for provenance (`labs/agents/critic.py:55`; `tests/test_critic.py:70`).

## Prompt Experiment Harness
- Loads prompt batches, reuses the shared validator builder, and logs each run to JSON/JSONL outputs for later analysis (`labs/experiments/prompt_experiment.py:32`; `labs/experiments/prompt_experiment.py:58`).
- Requires a working MCP validator; outages propagate as failures rather than silent skips (`labs/experiments/prompt_experiment.py:25`; `tests/test_prompt_experiment.py:41`).

## Logging Utilities & Tests
- `log_jsonl` enforces directory creation and sorted JSON serialization so all agents share consistent logging semantics (`labs/logging.py:10`).
- Test suite now covers deterministic seeded output, mandatory MCP failures, and the updated logging layout (`tests/test_determinism.py:10`; `tests/test_critic.py:33`; `tests/test_pipeline.py:108`).
