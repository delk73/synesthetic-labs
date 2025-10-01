# Agent Snapshot (v0.3.3 External Generators, TCP-default, hardening)

## GeneratorAgent
- Uses `AssetAssembler` to emit canonical shader/tone/haptic/control/meta/modulation/rule sections with deterministic IDs and seeded timestamps (labs/generator/assembler.py:44-102; tests/test_determinism.py:6-20).
- Logs generated assets and validated experiment records to `meta/output/labs/generator.jsonl` with provenance metadata for downstream analyses (labs/agents/generator.py:37-104; tests/test_pipeline.py:93-138).

## ExternalGenerator
- Implements retry/backoff, provenance injection, and mock/live transport wiring for Gemini/OpenAI engines (labs/generator/external.py:27-401; tests/test_external_generator.py:16-82).
- Persists MCP-reviewed runs with attempt traces and structured `failure.reason/detail` when validation or transport errors occur (labs/generator/external.py:168-223; tests/test_pipeline.py:211-227).

## CriticAgent
- Checks required asset fields, invokes MCP validation (strict and relaxed modes), and records structured review payloads with `validation_reason` and `validation_error` metadata (labs/agents/critic.py:58-168; tests/test_pipeline.py:63-186).
- Provides patch rating stubs for RLHF hooks by logging rating records via the shared JSONL sink (labs/agents/critic.py:170-192; tests/test_patches.py:49-57).
- Socket failure detail logic exists but lacks dedicated test coverage, leaving the v0.3.3 `socket_unavailable` requirement open (docs/labs_spec.md:182; tests/test_critic.py:23-182).

## MCP Transports
- `build_validator_from_env` defaults to TCP, wiring STDIO and socket variants only when explicitly requested and sharing the 1 MiB payload guard (labs/mcp_stdio.py:129-190; labs/transport.py:9-47; tests/test_tcp.py:66-137; tests/test_socket.py:9-63).
- `resolve_mcp_endpoint` centralises endpoint resolution so both validators and the critic share deterministic transport provenance (labs/mcp_stdio.py:129-137; labs/agents/critic.py:68-84), though fallback behaviour still needs direct tests (tests/test_tcp.py:140-160).

## Patch Lifecycle
- Preview/apply/rate commands log structured JSONL entries and reuse the critic for validation and rating storage to seed RLHF data (labs/patches.py:19-83; tests/test_patches.py:7-57).

## CLI Orchestration
- `generate`, `critique`, `preview`, `apply`, and `rate` share validator setup, persistence helpers, and logging wiring across subcommands with relaxed-mode fallbacks (labs/cli.py:59-210; tests/test_pipeline.py:38-290).

## Logging & Persistence
- `log_jsonl` materialises output directories and appends deterministic JSON lines for generator, critic, patch, and external streams under `meta/output/labs/` (labs/logging.py:13-35; labs/generator/external.py:189-223).

## Environment & Docs
- README and env samples describe TCP as default and socket as optional with `LABS_FAIL_FAST` downgrading severity in relaxed mode (README.md:45-56; .env:5-24).
- `SYN_SCHEMAS_DIR` remains documented/forwarded despite v0.3.3’s cleanup requirement, signalling a divergence to resolve (docs/labs_spec.md:184; .example.env:13; labs/mcp_stdio.py:152-154).
