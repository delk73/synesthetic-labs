# Synesthetic Labs Agents (v0.1)

The v0.1 lab focuses on a single loop: generator → critic with MCP-backed validation. This snapshot reflects the current implementation in `labs/`.

## Design Principles
- Keep implementations simple, deterministic, and dependency-light (Python ≥3.11).
- Treat MCP adapters and `synesthetic-schemas` as the single source of truth for schema validation; current CLI ships with a passthrough stub until integration lands.
- Run agents through the containerized harness; `pytest` runs locally and via Docker for parity (`Dockerfile`, `docker-compose.yml`, `test.sh`).
- Persist experiment artefacts and traces under `meta/output/` with structured logging for auditability.

## Generator Agent (Implemented)
- Module: `labs/agents/generator.py` exposes `Generator`, `GeneratorConfig`, `GeneratorProposal`, and `PromptRepository`.
- Behaviour: loads prompts from `meta/prompts/`, hashes config, stamps UTC timestamps, and logs proposals via `labs.logging.FileLogSink`.
- Extensibility: accepts injected clock and log sink for deterministic testing; prompt repository path exposed through `path_for` for provenance.
- Tests: `tests/test_generator.py` covers provenance logging and missing prompt failures.

## Critic Agent (Implemented)
- Module: `labs/agents/critic.py` exposes `Critic`, `CriticConfig`, `CritiqueResult`, and `MCPValidationResult` plus `MCPAdapter` protocol.
- Behaviour: performs minimal sanity checks, delegates validation to an injected MCP adapter, logs outcomes with proposal + MCP references.
- Determinism: derives notes from static checks and adapter responses; accepts pluggable log sink.
- Tests: `tests/test_critic.py` exercises empty-parameter warnings and MCP failure handling.

## Generator → Critic Workflow
- CLI: `labs/cli.py` wires `PromptRepository`, `Generator`, and `Critic` with a default `PassthroughMCPAdapter` and writes JSONL traces to `meta/output/`.
- Integration: `tests/test_pipeline.py` runs the combined pipeline with stub MCP responses and verifies end-to-end logging.
- Logging utilities: `labs/logging.py` defines `FileLogSink` and `NullLogSink` used across agents.

## Backlog / Next Steps
- Track upcoming work (real MCP adapter, RLHF loop, lifecycle orchestration, dataset tooling) in `meta/backlog.md`.
- Replace the passthrough MCP stub with adapters wired to `synesthetic-schemas` once available.
