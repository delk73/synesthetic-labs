# Synesthetic Labs Agents (v0.1) — Audit Snapshot

## Generator Agent
- Loads JSON prompts from repo storage and shapes assets with config/dataset context (labs/agents/generator.py:33; labs/agents/generator.py:63; labs/agents/generator.py:121).
- Derives deterministic proposal IDs from prompt, timestamp, and config hash before logging JSONL output (labs/agents/generator.py:67; labs/agents/generator.py:91).
- Pytest fixture locks proposal structure, provenance fields, and log emission (tests/test_generator.py:11; tests/test_generator.py:49).

## Critic Agent
- Validates proposal structure, collects issues, and builds recommendations tied to proposal IDs (labs/agents/critic.py:36; labs/agents/critic.py:66; labs/agents/critic.py:102).
- Accepts an injectable MCP validator callable, otherwise records a skipped validation issue (labs/agents/critic.py:29; labs/agents/critic.py:82).
- Tests cover both failure detection and validator handoff happy path (tests/test_critic.py:9; tests/test_critic.py:25; tests/test_critic.py:52).

## Generator → Critic Workflow
- run_pipeline orchestrates generator then critic and appends combined JSONL records (labs/lifecycle/pipeline.py:17; labs/lifecycle/pipeline.py:54).
- Integration test asserts deterministic IDs, log creation, and validator invocation (tests/test_pipeline.py:28; tests/test_pipeline.py:54; tests/test_pipeline.py:68).

## CLI
- Subcommands generate/critique/pipeline parse inline or file-backed JSON payloads (labs/cli.py:30; labs/cli.py:52; labs/cli.py:90).
- Default CLI wiring instantiates CriticAgent without an MCP validator, so runs mark validation as skipped (labs/cli.py:81; labs/agents/critic.py:82).
- Current pytest suite targets agents and pipeline but omits CLI coverage (tests/test_generator.py:11; tests/test_pipeline.py:12).

## Logging & Artefacts
- log_jsonl centralises JSONL emission with stable ordering under meta/output (labs/logging.py:6; labs/logging.py:11).
- Agents and pipeline append structured traces for audit replay (labs/agents/generator.py:91; labs/agents/critic.py:59; labs/lifecycle/pipeline.py:54).

## Outstanding gaps
- No synesthetic-schemas-backed validator module or dependency despite spec requirement (meta/prompts/init.json:7; requirements.txt:1).
- MCP adapter configuration is absent from default CLI flows, leaving validation skipped unless callers inject their own validator (labs/cli.py:81; labs/agents/critic.py:82).
- CLI subcommands lack automated tests to guard argument handling and logging (labs/cli.py:30; tests/test_generator.py:11).
