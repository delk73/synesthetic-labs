# Agent Snapshot (v0.2-TCP)

*Generator, critic, transports, and lifecycle flows align with the v0.2-TCP baseline after TCP integration and modulation/rule bundle wiring.*

## GeneratorAgent
- `propose` assembles v0.2 assets with modulation and rule bundle sections while logging provenance to `generator.jsonl` (`labs/agents/generator.py:37-62`, `labs/generator/assembler.py:62-88`).
- Deterministic seeding and provenance metadata ensure reproducibility for persisted experiments (`labs/generator/assembler.py:44-92`, `labs/agents/generator.py:64-103`).

## AssetAssembler
- Collects shader/tone/haptic parameters for a `parameter_index` and prunes controls against that set (`labs/generator/assembler.py:56-113`).
- Emits modulation and rule bundle stubs alongside core sections with unified versioning (`labs/generator/assembler.py:62-88`).

## CriticAgent
- `review` enforces required keys, invokes MCP via the selected transport, and records structured error metadata for outages (`labs/agents/critic.py:45-159`).
- `record_rating` logs patch ratings into the critic stream for downstream RLHF hooks (`labs/agents/critic.py:137-159`, `tests/test_ratings.py:6-21`).

## MCP Transports
- STDIO adapter launches the configured command with schema path normalization (`labs/mcp_stdio.py:136-148`).
- Socket validator manages AF_UNIX connections with 1 MiB framing and cleanup (`labs/mcp_stdio.py:150-159`, `labs/mcp/socket_main.py:26-68`, `tests/test_socket.py:29-88`).
- TCP validator negotiates host/port connections and reuses shared framing with deterministic failure surfacing (`labs/mcp_stdio.py:131-159`, `labs/mcp/tcp_client.py:17-46`, `tests/test_tcp.py:18-110`).

## Patch Lifecycle
- `preview_patch`, `apply_patch`, and `rate_patch` emit structured JSONL entries under `meta/output/labs/patches.jsonl` while reusing the critic for validation/ratings (`labs/patches.py:18-90`, `tests/test_patches.py:18-84`).
- CLI subcommands share validator resolution with generate/critique for consistent MCP behavior (`labs/cli.py:97-176`, `tests/test_pipeline.py:136-175`).

## Logging & Persistence
- JSONL helper materializes directories and writes newline-delimited records for generator, critic, and lifecycle logs (`labs/logging.py:13-24`).
- CLI persists validated assets under `meta/output/labs/experiments/` and records experiment linkage for traceability (`labs/cli.py:101-143`, `labs/agents/generator.py:64-103`).

## Container & Path Guards
- Docker image provisions and runs as the non-root `labs` user to satisfy container hardening requirements (`Dockerfile:1-12`).
- Resource path normalization blocks traversal attempts before delegating to transports (`labs/core.py:9-28`, `tests/test_path_guard.py:8-32`).
