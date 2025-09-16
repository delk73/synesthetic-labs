# Synesthetic Labs Agents (v0.1) — Audit Snapshot

## Generator Agent
- Loads prompts from repo-stored JSON and supports config + dataset context shaping (labs/agents/generator.py:63-128; meta/prompts/init.json:1-34).
- Derives deterministic proposal IDs via config hash + timestamp and appends JSONL traces to meta/output (labs/agents/generator.py:64-92; labs/logging.py:6-15).
- Pytest coverage locks prompt assembly, provenance fields, and log emission (tests/test_generator.py:11-53).

## Critic Agent
- Reviews proposals, accumulates issues, and builds recommendations tied to proposal IDs (labs/agents/critic.py:36-79).
- Accepts an injectable MCP validator callable; when unset it records a skipped validation issue rather than passing assets (labs/agents/critic.py:82-99).
- Tests cover both failure detection and happy-path validation handoff (tests/test_critic.py:9-53).

## Generator → Critic Workflow
- run_pipeline orchestrates agents sequentially and writes combined records to meta/output/pipeline.log.jsonl (labs/lifecycle/pipeline.py:17-55).
- Integration test asserts deterministic IDs, log creation, and MCP validator invocation (tests/test_pipeline.py:12-70).

## CLI
- Subcommands generate/critique/pipeline parse inline or file-backed JSON for prompts, configs, and proposals (labs/cli.py:20-90).
- Current CLI wiring instantiates CriticAgent without an MCP validator, so default runs mark validation as skipped (labs/cli.py:66-90; labs/agents/critic.py:82-85).

## Logging & Artefacts
- log_jsonl helper centralises JSONL output with stable ordering to meta/output (labs/logging.py:6-15).
- README documents logging expectations consistent with the lab spec (README.md:34-35; docs/labs_spec.md:35-37).

## Outstanding gaps
- No synesthetic-schemas-backed validator module or dependency despite being called out in the spec (requirements.txt:1; labs/agents/critic.py:82-99).
- MCP adapter configuration is absent from default CLI flows, leaving validation skipped unless callers inject their own validator (labs/cli.py:66-90).
- CLI subcommands lack automated tests to guard argument handling and logging (tests/test_generator.py:11-53; tests/test_pipeline.py:12-70).
