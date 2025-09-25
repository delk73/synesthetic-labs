# Agent Snapshot (v0.3 External Generators Audit)

## GeneratorAgent
- Proposes assets through the AssetAssembler with prompt validation and provenance stamping (`labs/agents/generator.py:45`, `labs/agents/generator.py:55`).
- Logs generated assets and experiment records to `meta/output/labs/generator.jsonl` for traceability (`labs/agents/generator.py:60`, `labs/agents/generator.py:98`).

## ExternalGenerator
- Provides retry/backoff generation with normalized assets and attempt traces (`labs/generator/external.py:97`, `labs/generator/external.py:147`).
- Persists successful runs and validation outcomes to `meta/output/labs/external.jsonl` (`labs/generator/external.py:159`, `labs/logging.py:30`).
- Records API failures with structured payloads for post-mortem review (`labs/generator/external.py:197`).
- Gemini/OpenAI subclasses supply mock responses and engine-specific provenance defaults (`labs/generator/external.py:328`, `labs/generator/external.py:382`).

## CriticAgent
- Validates required fields, invokes MCP transports, and emits structured validation metadata (`labs/agents/critic.py:34`, `labs/agents/critic.py:104`, `labs/agents/critic.py:148`).
- Supports fail-fast configuration yet currently allows validation skips in relaxed mode (divergent) (`labs/agents/critic.py:93`, `labs/agents/critic.py:118`).
- Logs patch ratings for downstream RLHF hooks (`labs/agents/critic.py:170`, `labs/agents/critic.py:185`).

## MCP Transports
- STDIO, socket, and TCP validators are selectable via environment configuration (`labs/mcp_stdio.py:134`, `labs/mcp_stdio.py:148`, `labs/mcp_stdio.py:159`).
- TCP client handles payload caps and connection failures via `MCPUnavailableError` (`labs/mcp/tcp_client.py:33`).
- Unix socket tests remain environment-gated and skipped by default (divergent) (`tests/test_socket.py:12`).

## Patch Lifecycle
- Preview/apply/rate workflows log structured events and reuse the critic for validation and ratings (`labs/patches.py:26`, `labs/patches.py:57`, `labs/patches.py:82`).
- Test suite verifies lifecycle logging and critic integration (`tests/test_patches.py:16`, `tests/test_patches.py:43`, `tests/test_patches.py:54`).

## CLI Orchestration
- `generate --engine` routes external assets through critic review and persistence (`labs/cli.py:77`, `labs/cli.py:126`, `labs/cli.py:136`).
- Other subcommands (`critique`, `preview`, `apply`, `rate`) share validator setup and logging helpers (`labs/cli.py:161`, `labs/cli.py:179`, `labs/cli.py:186`, `labs/cli.py:201`).

## Logging & Persistence
- Shared JSONL helper materializes directories and writes newline-delimited records (`labs/logging.py:13`).
- Generator, critic, patch, and external streams reside under `meta/output/labs/` for unified auditing (`labs/agents/generator.py:60`, `labs/agents/critic.py:160`, `labs/patches.py:64`, `labs/generator/external.py:195`).
