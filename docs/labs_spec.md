# synesthetic-labs Lab Spec (v0.1 Generator + Critic)

## Purpose
- Deliver the first generator + critic workflow for **Synesthetic System** asset experiments.
- Provide a safe playground for proposing assets while validation and persistence continue to live in `synesthetic-mcp` and `sdfk-backend`.
- Labs does not replace the validation or persistence responsibilities owned by MCP adapters and backend services.

## Scope (v0.1)
- Implement a generator agent interface for producing candidate assets/patches.
- Implement a critic agent that reviews generator output, surfaces issues, and prepares payloads while deferring schema authority to MCP validation.
- Wire generator → critic handoff with hooks for MCP adapter validation.
- Maintain repo structure needed to support these experiments (labs modules, tests, Docker harness).

## Non-Scope (Deferred to v0.2+)
- RLHF rating loops or scorer agents.
- Full patch lifecycle orchestration (propose → validate → rate → persist) and JSON Patch application flows.
- Dataset building, replay pipelines, or broader multimodal training assets.
- Automation of persistence into backend stores beyond MCP-mediated validation.
- Backlog items earmarked for v0.2+: RLHF loop integration, JSON Patch lifecycle orchestration, and dataset tooling improvements.

## Component Overview
| Component | Responsibilities | Interfaces |
| --- | --- | --- |
| Generator agent | Produce candidate shaders/tones/haptics or other multimodal assets for review. | Consumes prompts/specs; outputs asset proposals for critic review. |
| Critic agent | Analyze generator output, surface issues, and prepare artifacts for MCP validation while recognizing MCP as the final schema authority. | Receives generator output; emits critique notes and validation-ready payloads handed to MCP adapters. |
| Labs CLI (placeholder) | Entry point for running generator → critic experiments locally or in container. | MVP flow runs generator → critic → logging pipeline and exposes structured logging hooks. |

- Critic agent must attempt MCP schema validation by default, log `validation skipped` when the adapter is unavailable, and persist successful validator responses inside the review payload.

## Planned Features (v0.1)
- Configurable generator prompts housed under `meta/prompts/` for reproducible experiments.
- Critic prepares assets and calls MCP validation hooks before persistence.
- Structured logging backed by files in `meta/output/` to trace generator prompts, critic feedback, and MCP responses.
- Pytest-based coverage in `tests/test_agents.py` targeting generator + critic interactions.

## Logging
- Capture generator inputs, produced assets, critic findings, and MCP validation results in structured JSON (JSONL recommended).
- Store experiment logs under `meta/output/` with timestamps to enable replay.
- Ensure logs are reproducible across local runs and containerized workflows.

## Tests
- Unit tests for generator prompt assembly and output shaping in `tests/test_generator.py`.
- Unit tests for critic review shaping and payload preparation in `tests/test_critic.py`.
- Integration tests that exercise generator → critic handoffs and mocked MCP validation responses.
- End-to-end pipeline coverage in `tests/test_pipeline.py` validating generator → critic → MCP hooks.
- Containerized test harness (`./test.sh`) remains the path-to-green; local `pytest` runs are supported for rapid iteration.

## Constraints
- ⚠️ Early-stage project: repo structure and interfaces may change as generator + critic mature.
- MCP adapter must remain the gatekeeper for validation; labs should not bypass schema enforcement.
- Containerization is the default execution path; ensure parity between local and Docker-based workflows.
- Labs must log every generator and critic run; silent failures are not permitted.

## Exit Criteria
- Generator and critic agents run end-to-end locally and inside Docker with structured logs emitted.
- Critic output is compatible with MCP validation, blocking assets that fail schema checks.
- Tests covering generator + critic interactions pass in CI.
- Labs CLI entrypoint is documented in `README.md` and runs successfully in CI.
- Backlog items for v0.2+ (see Non-Scope) are confirmed and tracked in `meta/backlog.md` or the GitHub issues backlog.
