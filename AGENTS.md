# Agent Snapshot (v0.2 Alignment)

*Transport, patch lifecycle, and rating stubs verified against visible source, tests, and docs.*

## GeneratorAgent
- `propose` assembles full assets and logs each proposal to the generator stream (labs/agents/generator.py:37, labs/agents/generator.py:60).
- Deterministic provenance annotates generator version/seed for downstream traceability (labs/agents/generator.py:29, labs/agents/generator.py:54).
- `record_experiment` links validation outcomes back to persisted experiment paths (labs/agents/generator.py:78, labs/agents/generator.py:98).

## AssetAssembler
- Collects shader/tone/haptic parameters and prunes control mappings to known surfaces (labs/generator/assembler.py:56, labs/generator/assembler.py:104).
- Emits provenance with assembled timestamp and seed to keep validated runs reproducible (labs/generator/assembler.py:67).

## CriticAgent
- `review` accepts optional `patch_id`, forwarding assets through the configured MCP validator while logging results (labs/agents/critic.py:45, labs/agents/critic.py:118).
- `record_rating` writes structured rating stubs with patch/asset linkage to `critic.jsonl` (labs/agents/critic.py:137, labs/agents/critic.py:159).
- Fail-fast vs. relaxed behavior continues to hinge on `LABS_FAIL_FAST` (labs/agents/critic.py:62).

## MCP Bridge & Transports
- Shared framing enforces a 1 MiB cap across transports (`encode_payload`/`read_message`) (labs/transport.py:27, labs/transport.py:53).
- `build_validator_from_env` normalizes schema and socket paths before constructing STDIO or Unix socket validators (labs/mcp_stdio.py:131, labs/mcp_stdio.py:158).
- `SocketMCPValidator` drives AF_UNIX handshakes and surfaces connection/time-out failures consistently (labs/mcp_stdio.py:96, labs/mcp_stdio.py:122).
- `python -m labs.mcp` now dispatches to the socket adapter when `MCP_ENDPOINT=socket` (labs/mcp/__main__.py:12).
- `labs/mcp/socket_main.serve_once` guards payload size, handles unlink semantics, and reuses the stub response (labs/mcp/socket_main.py:20, labs/mcp/socket_main.py:41).

## Patch Lifecycle
- `preview_patch`, `apply_patch`, and `rate_patch` log structured lifecycle entries to `patches.jsonl` and reuse the critic for validation/ratings (labs/patches.py:18, labs/patches.py:65, labs/patches.py:78).
- CLI subcommands `preview`, `apply`, and `rate` expose the lifecycle, sharing the validator resolution path with generate/critique (labs/cli.py:82, labs/cli.py:150, labs/cli.py:172).

## Logging
- Generator, critic, and patch lifecycle logs remain under `meta/output/labs/`, with rating stubs recorded in the critic stream (labs/agents/generator.py:12, labs/agents/critic.py:13, labs/patches.py:11).
- Unix socket adapter teardown unlinks the socket path after each request, preventing stale endpoints (labs/mcp/socket_main.py:42).

## Container & Path Guards
- Docker image now provisions a non-root `labs` user and runs tests under that account (Dockerfile:3, Dockerfile:11).
- `normalize_resource_path` rejects traversal attempts before forwarding schema or socket paths to transports (labs/core.py:12, labs/mcp_stdio.py:145).
