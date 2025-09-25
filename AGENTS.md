# Agent Snapshot (v0.2-TCP Audit)

*Generator/critic stack remains deterministic with STDIO/Unix socket MCP validation, but TCP transport and v0.2 modulation updates are outstanding.*

## GeneratorAgent
- `propose` assembles and logs full assets with provenance entry `generator.version = v0.1` (`labs/agents/generator.py:37-62`).
- `record_experiment` appends validation outcomes and persisted paths to the generator log (`labs/agents/generator.py:64-103`).
- Gap: generator still instantiates `AssetAssembler(version="v0.1")`, so modulation and rule bundle stubs never appear in outputs (`labs/agents/generator.py:29-35`, `tests/test_generator_assembler.py:32-38`).

## AssetAssembler
- Collects shader/tone/haptic parameters into `parameter_index` and prunes mappings against that set (`labs/generator/assembler.py:56-113`).
- Emits provenance with assembler version, timestamp, and seed for reproducibility (`labs/generator/assembler.py:62-72`).
- Missing: assembled assets omit the v0.2 modulation and rule bundle sections required by the spec (`labs/generator/assembler.py:62-79`, `docs/labs_spec.md:80-81`).

## CriticAgent
- `review` enforces required keys, forwards assets to MCP, and records validation outcomes with fail-fast control (`labs/agents/critic.py:45-135`).
- `record_rating` writes structured rating stubs linked to optional assets (`labs/agents/critic.py:137-159`).
- Relaxed mode skips MCP when unavailable, logging the skip reason for traceability (`labs/agents/critic.py:68-109`, `tests/test_pipeline.py:104-150`).
- Outstanding: critic does not emit the structured TCP failure reason codes promised in the spec (`labs/agents/critic.py:118-135`, `docs/labs_spec.md:133-141`).

## MCP Bridge & Transports
- Shared framing enforces a 1 MiB cap for STDIO and socket payloads (`labs/transport.py:1-69`).
- `build_validator_from_env` supports STDIO via `MCP_ADAPTER_CMD` and Unix sockets via `MCP_SOCKET_PATH`, normalizing paths before use (`labs/mcp_stdio.py:134-159`).
- Socket adapter unlinks stale paths and handles oversize payloads deterministically (`labs/mcp/socket_main.py:17-68`, `tests/test_socket.py:29-69`).
- Missing: there is no `TcpMCPValidator`, and `MCP_ENDPOINT=tcp` is rejected despite `.env` advertising the mode (`labs/mcp_stdio.py:131-161`, `.env:5-12`).

## Patch Lifecycle
- `preview_patch`, `apply_patch`, and `rate_patch` write structured lifecycle events to `meta/output/labs/patches.jsonl` and reuse the critic for validation/ratings (`labs/patches.py:18-90`).
- CLI subcommands delegate directly to these helpers, sharing validator resolution with the generate/critique flow (`labs/cli.py:150-176`).

## Logging
- JSONL writer guarantees newline-delimited records and auto-creates directories (`labs/logging.py:13-24`).
- Generator, critic, and patch lifecycle logs land under `meta/output/labs/` with provenance fields intact (`labs/agents/generator.py:60-103`, `labs/agents/critic.py:118-159`, `labs/patches.py:26-89`).
- MCP outages surface in critic logs but without structured TCP-specific metadata yet (`labs/agents/critic.py:88-135`).

## Container & Path Guards
- Docker image runs as a non-root `labs` user for spec compliance (`Dockerfile:1-12`).
- `normalize_resource_path` rejects traversal before forwarding schema or socket paths to transports (`labs/core.py:9-28`, `tests/test_path_guard.py:8-32`).
