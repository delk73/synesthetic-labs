# Agent Snapshot (v0.3.1 External Generators Audit)

## GeneratorAgent
- Assembles canonical shader/tone/haptic/control/meta/modulation/rule sections with provenance and deterministic IDs when seeded (`labs/generator/assembler.py:56`, `labs/generator/assembler.py:75`).
- Logs generated assets and experiment records to `meta/output/labs/generator.jsonl` for traceability (`labs/agents/generator.py:70`, `labs/agents/generator.py:98`).

## ExternalGenerator
- Implements retry/backoff with attempt traces, provenance injection, and CLI wiring for Gemini/OpenAI engines (`labs/generator/external.py:90`, `labs/generator/external.py:168`, `labs/cli.py:108`).
- Success paths persist MCP results plus optional `failure.reason/detail` for validation misses; divergence: `record_failure` omits structured reason/detail for transport outages (`labs/generator/external.py:189`, `labs/generator/external.py:197`).

## CriticAgent
- Validates required keys, invokes MCP transports, and emits structured `validation_error` data with reason/detail (`labs/agents/critic.py:58`, `labs/agents/critic.py:140`).
- Divergence: relaxed mode skips MCP invocation entirely when `_build_validator_optional` returns `None` (`labs/agents/critic.py:100`, `tests/test_critic.py:153`).
- Records rating stubs for downstream RLHF hooks (`labs/agents/critic.py:170`, `tests/test_patches.py:54`).

## MCP Transports
- STDIO, socket, and TCP validators share a 1 MiB payload cap and raise `MCPUnavailableError` on transport failures (`labs/mcp_stdio.py:134`, `labs/mcp_stdio.py:148`, `labs/mcp_stdio.py:159`, `labs/transport.py:8`).
- Divergence: default transport still resolves to STDIO via `MCP_ENDPOINT` fallback instead of spec-mandated TCP (`labs/mcp_stdio.py:132`, `.example.env:1`).
- Socket tests remain gated behind `LABS_SOCKET_TESTS`, requiring documentation of optional status (`tests/test_socket.py:12`).

## Patch Lifecycle
- Preview/apply/rate stubs log structured JSONL records and reuse the critic for validation and rating storage (`labs/patches.py:26`, `labs/patches.py:57`, `labs/patches.py:82`, `tests/test_patches.py:11`).

## CLI Orchestration
- `generate`, `critique`, `preview`, `apply`, and `rate` subcommands share validator setup, persistence, and logging helpers (`labs/cli.py:77`, `labs/cli.py:101`, `labs/cli.py:179`, `labs/cli.py:186`, `labs/cli.py:201`).
- Divergence: `_build_validator_optional` allows validation skips when fail-fast is disabled, breaking the MCP-always requirement (`labs/cli.py:59`, `tests/test_pipeline.py:63`).

## Logging & Persistence
- `log_jsonl` materialises directories and writes newline-delimited JSON; generator, critic, patch, and external streams land under `meta/output/labs/` (`labs/logging.py:21`, `labs/agents/generator.py:70`, `labs/agents/critic.py:160`, `labs/patches.py:64`, `labs/generator/external.py:195`).
- Divergence: external transport failures only capture `status`/`error` without reason/detail, violating logging requirements (`labs/generator/external.py:197`).

## Environment & Docs
- Env samples still expose unused backend knobs and advertise STDIO as the default transport, contrary to v0.3.1 mandates (`.env:28`, `.example.env:1`, `README.md:31`).
