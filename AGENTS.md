# Synesthetic Labs Agents (v0.1)

This snapshot captures the simplified generator → critic loop shipped in
version 0.1. The code favours determinism, minimal dependencies, and structured
JSONL logging so audits can replay activity from `meta/output/`.

## Generator Agent
- Module: `labs/agents/generator.py` exposing `GeneratorAgent`.
- Behaviour: validates non-empty prompts, stamps UTC timestamps, assigns UUIDs,
  and emits provenance describing the agent, version, and log destination.
- Logging: appends `generator.propose` events via `labs.logging.log_jsonl`.
- Tests: `tests/test_generator.py` ensures proposals include required keys and
  that JSONL logging occurs.

## Critic Agent
- Module: `labs/agents/critic.py` exposing `CriticAgent`.
- Behaviour: verifies generator assets contain id, timestamp, prompt, and
  provenance; validates timestamp format and non-empty prompt content.
- Logging: appends `critic.review` events via `labs.logging.log_jsonl` and logs
  outcomes through the standard library `logging` module.
- Tests: `tests/test_critic.py` covers missing field detection and successful
  reviews.

## Generator → Critic Workflow
- CLI: `labs/cli.py` offers `generate` and `critique` subcommands for manual
  operation, printing JSON payloads to stdout.
- Integration: `tests/test_pipeline.py` exercises the round-trip pipeline with a
  shared JSONL log file to confirm provenance and critic status propagation.
- Runtime: The repo supplies Docker and GitHub Actions harnesses to run the
  pytest suite consistently.

## Provenance
- Prompt baseline defined in `meta/prompts/init.json` (immutable per spec).
- Audit performed manually against `meta/prompts/audit.json` requirements on
  2025-09-16T14:59:49Z and recorded in `meta/output/labs_state.md`.
