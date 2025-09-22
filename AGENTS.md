# Agent Snapshot (v0.1 Audit)

## GeneratorAgent
- `propose` emits prompt-only envelopes and skips shader/tone/haptic assembly, leaving downstream code to call the assembler separately (`labs/agents/generator.py:30`, `labs/generator/assembler.py:38`, `tests/test_pipeline.py:18`).
- Default provenance marks version `v0.3`, diverting from the v0.1 target but still logging UUID/ISO timestamps to `meta/output/labs/generator.jsonl` (`labs/agents/generator.py:12`, `labs/agents/generator.py:25`, `tests/test_generator.py:10`).
- `record_experiment` captures critic outcomes, persisted asset paths, and source timestamps for replayability (`labs/agents/generator.py:71`, `tests/test_generator.py:27`).

## AssetAssembler
- Clones shader, tone, haptic, control, and meta generators, then produces a parameter index and prunes dangling mappings before returning the asset (`labs/generator/assembler.py:32`, `labs/generator/assembler.py:56`, `labs/generator/assembler.py:108`).
- Deterministic identifiers derive from prompt/seed/version hashes, guaranteeing byte-identical payloads in seeded runs (`labs/generator/assembler.py:44`, `tests/test_determinism.py:10`).
- Provenance on each asset records assembler name, version, timestamp, and seed for audit trails (`labs/generator/assembler.py:62`, `labs/generator/assembler.py:71`).

## CriticAgent
- Guards required fields before validation and caches the STDIO validator built from environment variables (`labs/agents/critic.py:21`, `labs/agents/critic.py:49`).
- Surfaces MCP outages as review failures while logging responses and issues to `meta/output/labs/critic.jsonl` (`labs/agents/critic.py:66`, `labs/agents/critic.py:82`, `tests/test_critic.py:48`).

## MCP Bridge & CLI
- `build_validator_from_env` requires `MCP_ADAPTER_CMD`, injects optional schema paths, and raises on launch/timeouts/malformed payloads (`labs/mcp_stdio.py:84`, `labs/mcp_stdio.py:64`).
- CLI `generate` composes assets through `AssetAssembler` before invoking the critic and persisting validated outputs to `meta/output/labs/experiments/` (`labs/cli.py:74`, `labs/cli.py:89`, `tests/test_pipeline.py:58`).
- CLI `critique` exits non-zero whenever MCP validation cannot run, matching the fail-fast spec (`labs/cli.py:110`, `tests/test_pipeline.py:33`).

## Prompt Experiment Harness
- Loads prompts, reuses the shared validator builder, and writes per-run JSON and JSONL artefacts for later analysis (`labs/experiments/prompt_experiment.py:32`, `labs/experiments/prompt_experiment.py:52`).
- Currently drives `GeneratorAgent.propose`, so generated assets contain metadata only before MCP review, diverging from the canonical section expectations (`labs/experiments/prompt_experiment.py:34`, `labs/agents/generator.py:30`).

## Logging Utilities & Tests
- `log_jsonl` guarantees directory creation and sorted JSON serialization for shared logging semantics (`labs/logging.py:10`).
- Test suite covers generator logging, critic failure handling, CLI persistence, and assembler determinism (`tests/test_generator.py:10`, `tests/test_critic.py:48`, `tests/test_pipeline.py:58`, `tests/test_determinism.py:10`).
