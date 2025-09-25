# Agent Snapshot (v0.3.1 External Generators Audit)

## GeneratorAgent
- Uses `AssetAssembler` to emit canonical shader/tone/haptic/control/meta/modulation/rule sections with deterministic IDs and seeded timestamps (`labs/generator/assembler.py:44`, `tests/test_determinism.py:10`).
- Logs generated assets and validated experiment records to `meta/output/labs/generator.jsonl` with provenance metadata for downstream analyses (`labs/agents/generator.py:60`, `tests/test_pipeline.py:137`).

## ExternalGenerator
- Implements retry/backoff, provenance injection, and mock/live transport wiring for Gemini/OpenAI engines (`labs/generator/external.py:75`, `labs/generator/external.py:332`).
- Persists MCP-reviewed runs with attempt traces and structured `failure.reason/detail` when validation or transport errors occur (`labs/generator/external.py:168`, `tests/test_external_generator.py:40`).

## CriticAgent
- Checks required asset fields, invokes MCP validation (strict and relaxed modes), and records structured review payloads with `validation_reason` and `validation_error` metadata (`labs/agents/critic.py:58`, `tests/test_critic.py:53`).
- Provides patch rating stubs for RLHF hooks by logging rating records via the shared JSONL sink (`labs/agents/critic.py:171`, `tests/test_patches.py:54`).
- Divergence: error detail still reports `stdio_unavailable` even when TCP is the active default transport, obscuring transport provenance in logs (`labs/agents/critic.py:68`).

## MCP Transports
- `build_validator_from_env` defaults to TCP, falling back to STDIO or socket only when explicitly requested and reusing the shared 1 MiB payload guard (`labs/mcp_stdio.py:132`, `labs/transport.py:8`).
- TCP validator handles round-trips, oversize payloads, and connection errors with `MCPUnavailableError` surfaces (`labs/mcp/tcp_client.py:24`, `tests/test_tcp.py:110`).
- Divergence: Critic’s `validation_error.detail` derives from the raw `MCP_ENDPOINT` env and mislabels TCP outages as STDIO failures (`labs/agents/critic.py:68`).

## Patch Lifecycle
- Preview/apply/rate commands log structured JSONL entries and reuse the critic for validation and rating storage to seed RLHF data (`labs/patches.py:26`, `labs/patches.py:68`, `tests/test_patches.py:25`).

## CLI Orchestration
- `generate`, `critique`, `preview`, `apply`, and `rate` share validator setup, persistence helpers, and logging wiring across subcommands (`labs/cli.py:59`, `labs/cli.py:108`, `labs/cli.py:177`).

## Logging & Persistence
- `log_jsonl` materialises output directories and appends deterministic JSON lines for generator, critic, patch, and external streams under `meta/output/labs/` (`labs/logging.py:13`, `labs/generator/external.py:195`).

## Environment & Docs
- README documents TCP-as-default, socket optionality, and relaxed-mode behaviour, but `.env` and the critic docstring still describe relaxed mode as skipping validation (`README.md:31`, `.env:17`, `labs/agents/critic.py:46`).
