# Agent Snapshot (v0.1 Audit)

## GeneratorAgent
- `propose` delegates to AssetAssembler so every prompt yields shader/tone/haptic/control/meta sections plus provenance (labs/agents/generator.py:37, labs/generator/assembler.py:38, tests/test_generator.py:24).
- `record_experiment` appends validation outcomes with timestamps and persisted paths to the generator log stream (labs/agents/generator.py:64, labs/logging.py:10, tests/test_generator.py:40).
- Default logging sinks under `meta/output/labs/` capture both raw assets and experiment summaries for replay (labs/agents/generator.py:12, labs/agents/generator.py:60).

## AssetAssembler
- Clones component generators, collects parameter indexes, and filters control mappings to reference only known parameters (labs/generator/assembler.py:50, labs/generator/assembler.py:58, tests/test_generator_assembler.py:32).
- Deterministic identifiers derive from prompt/seed/version hashes, ensuring seeded runs reproduce IDs and timestamps (labs/generator/assembler.py:84, tests/test_determinism.py:10).
- Asset provenance includes assembler agent/version, timestamp, and seed for audit trails (labs/generator/assembler.py:67, labs/generator/assembler.py:70).

## CriticAgent
- Validates required asset fields before invoking MCP, surfacing structural issues immediately (labs/agents/critic.py:41, tests/test_critic.py:23).
- Lazily builds and caches the STDIO validator, so repeated reviews reuse the same MCP subprocess wiring (labs/agents/critic.py:48, labs/agents/critic.py:61).
- Logs review payloads, including MCP responses and outages, to `meta/output/labs/critic.jsonl` (labs/agents/critic.py:12, labs/agents/critic.py:66, tests/test_critic.py:48).

## MCP Bridge & CLI
- `build_validator_from_env` enforces `MCP_ADAPTER_CMD` and forwards optional schema paths before spawning the STDIO adapter (labs/mcp_stdio.py:84, labs/mcp_stdio.py:93, tests/test_critic.py:95).
- CLI `generate` composes assets, runs MCP validation, and persists validated payloads with relative experiment paths (labs/cli.py:73, labs/cli.py:87, tests/test_pipeline.py:62).
- CLI `critique` returns non-zero when MCP cannot launch, matching the fail-fast policy (labs/cli.py:105, tests/test_pipeline.py:37).

## Prompt Experiment Harness
- Loads prompt batches, generates canonical assets, and runs CriticAgent with the shared validator builder (labs/experiments/prompt_experiment.py:41, labs/experiments/prompt_experiment.py:58, tests/test_prompt_experiment.py:12).
- Persists per-run JSON summaries, raw assets, and optional validated responses for downstream analysis (labs/experiments/prompt_experiment.py:68, labs/experiments/prompt_experiment.py:86, labs/experiments/prompt_experiment.py:96).
- Records experiment metadata back through GeneratorAgent to keep logs consistent across CLI and harness flows (labs/experiments/prompt_experiment.py:90, labs/agents/generator.py:64).

## Logging Utilities & Tests
- `log_jsonl` guarantees directory creation and sorted JSON serialization, underpinning generator/critic log streams (labs/logging.py:10).
- Test suite covers component generators, assembler wiring, critic failure handling, CLI persistence, deterministic IDs, and the prompt experiment pipeline (tests/test_generator_components.py:53, tests/test_generator_assembler.py:21, tests/test_critic.py:48, tests/test_pipeline.py:62, tests/test_determinism.py:10, tests/test_prompt_experiment.py:12).
