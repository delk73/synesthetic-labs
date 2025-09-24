## Summary of repo state
- MCP validation supports both STDIO and Unix socket transports with shared 1 MiB framing (labs/mcp_stdio.py:96, labs/transport.py:27).
- Patch lifecycle commands preview, apply, and rate patches while logging results to both patch and critic streams (labs/cli.py:82, labs/patches.py:68, labs/agents/critic.py:137).
- Container runs as a non-root user and path normalization rejects traversal in schema/socket configuration (Dockerfile:1, labs/core.py:12).
- Modulation and rule bundle stubs remain absent from the assembled asset despite v0.2 baseline expectations (labs/generator/assembler.py:62).

## Top gaps & fixes (3-5 bullets)
- Integrate modulation and rule bundle stubs into AssetAssembler with updated tests to satisfy the v0.2 baseline.
- Extend socket adapter coverage to exercise success path when Unix sockets are permitted outside the sandbox environment.
- Document expected patch update schema (shape of `updates`) to guide future orchestration work.

## Alignment with labs_spec.md
| Spec item | Status | Evidence |
| --- | --- | --- |
| STDIO MCP validation | Present | `StdioMCPValidator.validate` enforces size cap and returns adapter payloads (labs/mcp_stdio.py:49).
| Unix socket MCP transport | Present | `SocketMCPValidator` and `labs/mcp/socket_main.serve_once` handle AF_UNIX validation loops (labs/mcp_stdio.py:96, labs/mcp/socket_main.py:20).
| Patch lifecycle (preview/apply/rate) | Present | Stub orchestrations log preview/apply/rate events and reuse CriticAgent (labs/patches.py:18, labs/patches.py:37, labs/patches.py:68).
| Critic ratings stub logging | Present | `CriticAgent.record_rating` writes rating entries to `critic.jsonl` (labs/agents/critic.py:137).
| Modulation stub in baseline | Missing | Assembler output stops at shader/tone/haptic/control/meta (labs/generator/assembler.py:62).
| Rule bundle stub in baseline | Missing | No rule bundle emitted; tests still assert absence (tests/test_generator_assembler.py:35).
| Path normalization / traversal guard | Present | `normalize_resource_path` rejects `..` segments before transport configuration (labs/core.py:12, labs/mcp_stdio.py:145).
| Container non-root hardening | Present | Dockerfile provisions and switches to user `labs` before running tests (Dockerfile:1, Dockerfile:11).
| Logging JSONL under meta/output | Present | Generator, critic, and patch lifecycle logs target `meta/output/labs/` sinks (labs/agents/generator.py:12, labs/agents/critic.py:13, labs/patches.py:11).
| Docs reflect socket + patch workflows | Present | README documents new CLI commands and socket transport options (README.md:16).

## Generator implementation
| Component | Status | Evidence |
| --- | --- | --- |
| ShaderGenerator | Present | Emits CircleSDF shader with uniforms and inputs (labs/generator/shader.py:45).
| ToneGenerator | Present | Returns Tone.Synth configuration with envelope/effects (labs/generator/tone.py:34).
| HapticGenerator | Present | Provides generic haptic profile (labs/generator/haptic.py:34).
| ControlGenerator | Present | Mouse mappings wired to shader parameters (labs/generator/control.py:19).
| MetaGenerator | Present | Supplies canonical metadata fields (labs/generator/meta.py:17).
| Modulation integration | Missing | No modulation component is assembled (labs/generator/assembler.py:62).
| Rule bundle integration | Missing | Rule bundle remains absent from assets (tests/test_generator_assembler.py:35).

## Critic implementation
| Responsibility | Status | Evidence |
| --- | --- | --- |
| Required field checks | Present | REQUIRED_KEYS enforced before validation (labs/agents/critic.py:33).
| Lazy MCP validator build | Present | Validator constructed and cached on demand (labs/agents/critic.py:68).
| Fail-fast vs relaxed toggle | Present | `LABS_FAIL_FAST` gate controls error vs skip (labs/agents/critic.py:62).
| Review logging with MCP payload | Present | Review entries recorded with MCP response/patch context (labs/agents/critic.py:118).
| Ratings stub logging | Present | `record_rating` logs structured patch ratings (labs/agents/critic.py:137).
| Patch validation before apply | Present | `apply_patch` invokes `CriticAgent.review` with `patch_id` metadata (labs/patches.py:54).

## Assembler / Wiring step
- Parameter index: `_collect_parameters` aggregates shader/tone/haptic parameters for later wiring (labs/generator/assembler.py:56).
- Dangling reference pruning: `_prune_controls` filters control mappings to known parameters (labs/generator/assembler.py:104).
- Provenance: Assets capture assembler agent, version, timestamp, and seed (labs/generator/assembler.py:67).

## Patch lifecycle
- Preview: `preview_patch` logs intent without mutating the asset (labs/patches.py:18).
- Apply: `apply_patch` merges updates, validates with CriticAgent, and logs review details (labs/patches.py:37).
- Rate stubs: `rate_patch` records ratings and forwards them to the critic log (labs/patches.py:68, labs/agents/critic.py:137).
- Logging: Lifecycle events append to `meta/output/labs/patches.jsonl` alongside critic review entries (labs/patches.py:57).

## MCP integration
- STDIO validation: `StdioMCPValidator` streams newline-delimited JSON with a 1 MiB cap (labs/mcp_stdio.py:49).
- Socket validation: Unix socket client/server pair exchanges framed JSON and unlinks endpoints after use (labs/mcp_stdio.py:96, labs/mcp/socket_main.py:20).
- Failure handling: MCPUnavailableError wraps timeouts, process failures, and socket errors (labs/mcp_stdio.py:83, labs/mcp_stdio.py:118).
- Strict vs relaxed mode: `_build_validator_optional` and `is_fail_fast_enabled` enforce the LABS_FAIL_FAST policy (labs/cli.py:58, labs/agents/critic.py:62).

## Test coverage
| Feature | Tested? | Evidence |
| --- | --- | --- |
| Generator emits sections & logs | Yes | `test_generator_propose_writes_log` validates asset structure/logging (tests/test_generator.py:9).
| Assembler parameter pruning | Yes | `test_asset_assembler_produces_consistent_payload` checks mappings vs parameters (tests/test_generator_assembler.py:21).
| Critic fail-fast handling | Yes | MCP outages surfaced in `test_validation_failure_when_mcp_unavailable` (tests/test_critic.py:90).
| CLI persistence flow | Yes | `test_cli_generate_persists_validated_asset` verifies saved experiments (tests/test_pipeline.py:92).
| Prompt experiment harness | Yes | Batch runner writes run and asset files (tests/test_prompt_experiment.py:12).
| Patch lifecycle integration | Yes | `tests/test_patches.py` covers preview/apply/rate stubs (tests/test_patches.py:9).
| Socket transport | Partial | `tests/test_socket.py` exercises round-trip and cap, skipping when sandbox denies AF_UNIX (tests/test_socket.py:24).
| Rating stub logging | Yes | `test_critic_records_rating` ensures critic log entries for ratings (tests/test_ratings.py:6).
| Path traversal rejection | Yes | `test_normalize_resource_path_rejects_traversal` rejects `..` segments (tests/test_path_guard.py:15).
| Container non-root enforcement | No | Covered indirectly via Dockerfile but not asserted in tests.

## Dependencies and runtime
| Package | Used in | Required/Optional |
| --- | --- | --- |
| pytest | Test suite runner invoked in CI (tests/**). | Required (requirements.txt:1).
| python:3.11-slim | Docker base image for containerized tests. | Required (Dockerfile:1).

## Environment variables
- `MCP_ENDPOINT`: `stdio` by default; set to `socket` to activate Unix transport (labs/mcp_stdio.py:134).
- `MCP_ADAPTER_CMD`: Required for STDIO adapter invocation (labs/mcp_stdio.py:136).
- `MCP_SOCKET_PATH`: Required when `MCP_ENDPOINT=socket`, normalized before use (labs/mcp_stdio.py:150).
- `SYN_SCHEMAS_DIR`: Optional schemas directory; normalized and forwarded to the adapter environment (labs/mcp_stdio.py:143).
- `LABS_EXPERIMENTS_DIR`: Controls experiment persistence location (labs/cli.py:33).
- `LABS_FAIL_FAST`: Toggles strict vs relaxed MCP handling (labs/agents/critic.py:20).

## Logging
- `log_jsonl` provides structured JSONL writing with directory creation (labs/logging.py:10).
- Generator proposals and experiment records stream to `meta/output/labs/generator.jsonl` (labs/agents/generator.py:12, labs/agents/generator.py:98).
- Critic reviews and ratings share the critic log sink `meta/output/labs/critic.jsonl` (labs/agents/critic.py:13, labs/agents/critic.py:137).
- Patch lifecycle actions append to `meta/output/labs/patches.jsonl` alongside critic review payloads (labs/patches.py:11, labs/patches.py:57).

## Documentation accuracy
- README documents socket transport configuration, patch lifecycle commands, and fail-fast semantics (README.md:16).
- labs_spec.md v0.2 scope reflects CLI orchestrations and logging requirements (docs/labs_spec.md:70).
- `.env.example` lists MCP_ENDPOINT/MCP_SOCKET_PATH alongside existing knobs (.env.example:1).

## Detected divergences
- Modulation and rule bundle stubs are still omitted from assembler output, diverging from the v0.2 baseline expectations (docs/labs_spec.md:78, labs/generator/assembler.py:62).
- Automated coverage cannot exercise Unix socket behavior in sandbox environments due to OS restrictions; socket tests skip accordingly (tests/test_socket.py:24).

## Recommendations
- Implement modulation and rule bundle generators in AssetAssembler, updating schema fixtures and assertions to meet the v0.2 baseline.
- Provide an opt-in integration test harness (or manual instructions) for Unix socket validation outside sandboxed CI to ensure end-to-end coverage.
- Expand documentation for patch `updates` schema and potential merge strategy to prepare for richer lifecycle orchestration.
