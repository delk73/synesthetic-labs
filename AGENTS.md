# Agent Snapshot (v0.2 Audit)

*Transport, patch lifecycle, and rating stubs verified against visible source, tests, and docs.*

## GeneratorAgent
- `propose` assembles full assets and logs each proposal to the generator stream (`labs/agents/generator.py`).
- Deterministic provenance annotates generator version/seed for downstream traceability (`labs/generator/assembler.py`).
- `record_experiment` links validation outcomes back to persisted experiment paths (`labs/agents/generator.py`).

## AssetAssembler
- Collects shader/tone/haptic parameters and prunes control mappings to known surfaces (`labs/generator/assembler.py`).
- Emits provenance with assembled timestamp and seed to keep validated runs reproducible (`labs/generator/assembler.py`).

## CriticAgent
- `review` accepts optional `patch_id`, forwarding assets through the configured MCP validator while logging results (`labs/agents/critic.py`).
- `record_rating` writes structured rating stubs with patch/asset linkage to `critic.jsonl` (`labs/agents/critic.py`).
- Fail-fast vs. relaxed behavior hinges on `LABS_FAIL_FAST` (`labs/agents/critic.py`).

## MCP Bridge & Transports
- Shared framing enforces a 1 MiB cap across transports (`labs/transport.py`).
- `build_validator_from_env` normalizes schema and socket paths before constructing STDIO or Unix socket validators (`labs/mcp_stdio.py`).
- `SocketMCPValidator` drives `AF_UNIX` handshakes and surfaces connection/time-out failures consistently (`labs/mcp_stdio.py`).
- `python -m labs.mcp` dispatches to the socket adapter when `MCP_ENDPOINT=socket` (`labs/mcp/__main__.py`).
- `labs/mcp/socket_main.serve_once` guards payload size, handles unlink semantics, and reuses the stub response (`labs/mcp/socket_main.py`).

## Patch Lifecycle
- `preview_patch`, `apply_patch`, and `rate_patch` log structured lifecycle entries to `patches.jsonl` and reuse the critic for validation/ratings (`labs/patches.py`).
- CLI subcommands `preview`, `apply`, and `rate` expose the lifecycle, sharing the validator resolution path with generate/critique (`labs/cli.py`).

## Logging
- Generator, critic, and patch lifecycle logs reside under `meta/output/labs/`.
- Rating stubs are recorded in the critic stream (`meta/output/labs/critic.jsonl`).

## Container & Path Guards
- Docker image provisions a non-root `labs` user (`Dockerfile:3`, `Dockerfile:11`).
- `normalize_resource_path` rejects traversal attempts before forwarding schema or socket paths to transports (`labs/core.py`).