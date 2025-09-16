# Synesthetic Labs Agents (v0.1)

The v0.1 lab focuses on a single loop: generator → critic with MCP-backed validation. This document summarizes what each agent is expected to do, how they interact, and the guardrails defined in `docs/labs_spec.md` and the initialization prompt.

## Design Principles
- Keep implementations simple, deterministic, and dependency-light (Python ≥3.11).
- Treat MCP adapters and `synesthetic-schemas` as the single source of truth for schema validation.
- Run agents through the containerized harness; the local `pytest` workflow must mirror Docker execution.
- Persist experiment artefacts and traces under `meta/output/` with structured logging so every run is auditable.

## Generator Agent
- **Goal**: propose candidate multimodal assets (e.g., shaders, tones, haptics) for critic review.
- **Inputs**: configuration + prompts from `meta/prompts/`, optional dataset context, and CLI/runtime flags.
- **Outputs**: structured proposals that include enough metadata for downstream validation and logging.
- **Responsibilities**:
  - Assemble reproducible prompts and seed data from repo-hosted sources.
  - Attach provenance info (prompt ID, timestamp, config hash) to each proposal before logging to `meta/output/`.
  - Hand off proposals to the critic without attempting schema validation locally.
- **Implementation notes**:
  - Provide a thin interface (class or protocol) to enable swapping generators as experiments evolve.
  - Surface hooks for injecting MCP adapter stubs during tests.
  - Ensure tests exercise prompt assembly and payload shaping (`tests/test_generator.py`).

## Critic Agent
- **Goal**: analyse generator output, highlight issues, and prepare payloads ready for MCP validation.
- **Inputs**: generator proposals plus any MCP adapter configuration provided by the runtime.
- **Outputs**: critique notes, recommended actions, and validation-ready payloads for MCP adapters.
- **Responsibilities**:
  - Perform lightweight sanity checks while deferring authoritative validation to MCP.
  - Generate structured feedback that maps back to the originating generator proposal.
  - Invoke MCP validation hooks (or mocks in tests) and propagate pass/fail status to logs.
  - Block or flag assets that fail MCP validation; never bypass schema enforcement.
- **Implementation notes**:
  - Maintain deterministic behaviour for reproducible test runs.
  - Ensure critic logging captures references to both the generator artefact and MCP response.
  - Cover review shaping and MCP handoff logic in `tests/test_critic.py`.

## Generator → Critic Workflow
1. CLI or lifecycle harness instantiates the generator with prompt/config context.
2. Generator emits proposal package(s) and writes initial trace entries.
3. Critic consumes proposals, attaches critiques, and calls MCP validation adapters.
4. Final combined artefacts (proposal, critique, MCP result) are persisted under `meta/output/`.
5. Integration tests (`tests/test_pipeline.py`) exercise the full path with mocked MCP responses.

## Container & Tooling Expectations
- `labs/cli.py` should expose a `--help` entry point for running the loop locally and inside Docker.
- `test.sh` remains the source of truth for path-to-green; it must build the container and run pytest.
- Keep agent interfaces stable enough for future lifecycle orchestration and dataset replay modules.
