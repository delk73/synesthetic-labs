# Agent Snapshot (v0.2-TCP)

*Generator, critic, transports, and lifecycle flows align with the v0.2-TCP baseline after adding TCP dispatch to the MCP bridge (`labs/mcp_stdio.py:159`).*

## GeneratorAgent
- `propose` assembles canonical sections, annotates provenance, and logs JSONL for traceability (`labs/agents/generator.py:37`; `labs/agents/generator.py:50`; `labs/agents/generator.py:60`).
- `record_experiment` links reviews to persisted experiment paths with validation metadata (`labs/agents/generator.py:64`; `labs/agents/generator.py:78`).

## AssetAssembler
- Collects shader/tone/haptic parameters and prunes dangling controls before returning assets (`labs/generator/assembler.py:64`; `labs/generator/assembler.py:114`).
- Emits modulation and rule bundle stubs alongside the core sections with consistent versioning (`labs/generator/assembler.py:41`; `labs/experimental/modulation.py:45`; `labs/experimental/rule_bundle.py:55`).

## CriticAgent
- `review` enforces required keys, invokes the configured MCP validator, and maps outages to structured `validation_error` payloads (`labs/agents/critic.py:58`; `labs/agents/critic.py:88`; `labs/agents/critic.py:70`).
- `record_rating` captures patch ratings for downstream RLHF hooks while writing to the critic log (`labs/agents/critic.py:170`; `tests/test_ratings.py:10`).
- `LABS_FAIL_FAST` toggles between failing on MCP outages and logging relaxed skips (`labs/agents/critic.py:63`; `tests/test_pipeline.py:151`).

## MCP Transports
- STDIO validator launches `MCP_ADAPTER_CMD` requests with schema path normalization (`labs/mcp_stdio.py:134`).
- Socket validator manages AF_UNIX connections with newline framing and cleanup (`labs/mcp_stdio.py:148`; `labs/mcp/socket_main.py:20`).
- TCP validator reuses shared framing and surfaces connection failures deterministically (`labs/mcp_stdio.py:159`; `labs/mcp/tcp_client.py:34`; `tests/test_tcp.py:66`).

## Patch Lifecycle
- `preview_patch`, `apply_patch`, and `rate_patch` reuse the critic for validation/ratings and append structured events to `meta/output/labs/patches.jsonl` (`labs/patches.py:26`; `labs/patches.py:54`; `labs/patches.py:78`).
- CLI subcommands share validator resolution to keep lifecycle behavior aligned with generator/critic flows (`labs/cli.py:97`; `labs/cli.py:157`; `labs/cli.py:172`).

## Logging & Persistence
- JSONL helper materializes directories and writes newline-delimited records for generator, critic, and lifecycle logs (`labs/logging.py:10`; `labs/agents/critic.py:160`; `labs/patches.py:64`).
- CLI persists validated assets under `meta/output/labs/experiments/` and records experiment linkage (`labs/cli.py:107`; `labs/cli.py:112`; `labs/agents/generator.py:98`).

## Container & Path Guards
- Docker image provisions and runs as the non-root `labs` user to satisfy hardening requirements (`Dockerfile:3`; `Dockerfile:13`).
- Resource path normalization blocks traversal before delegating to transports (`labs/core.py:12`; `tests/test_path_guard.py:16`).
