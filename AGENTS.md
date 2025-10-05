# Synesthetic Labs Agents (Schema Targeting Audit)

## Generator Agent — Present
- CLI exposes `--schema-version` with env precedence, and tests confirm prompt-to-asset flow across deterministic and external engines.【F:labs/cli.py†L52-L146】【F:tests/test_pipeline.py†L228-L317】
- AssetAssembler now defaults to 0.7.3, branches between legacy/enriched payloads, and tags hosted `$schema` URLs with coverage in the assembler tests.【F:labs/generator/assembler.py†L23-L209】【F:tests/test_generator_assembler.py†L1-L87】
- GeneratorAgent logging continues to capture schema_version, trace IDs, and validation outcomes for persisted experiments.【F:labs/agents/generator.py†L94-L195】【F:tests/test_generator.py†L11-L118】

## Critic Agent — Present
- Reviewer enforces required keys, resolves transport defaults, and surfaces `mcp_unavailable`/`mcp_error` reasons under strict vs relaxed modes.【F:labs/agents/critic.py†L61-L188】【F:tests/test_critic.py†L15-L204】
- Rating stubs reuse Critic logging metadata to keep RLHF artifacts tied to transports and strict flags.【F:labs/agents/critic.py†L190-L218】【F:tests/test_patches.py†L65-L92】

## MCP Resolver — Present
- `resolve_mcp_endpoint` defaults to TCP, validates stdio/socket prerequisites, and surfaces taxonomy-aligned errors with coverage locking the fallback behavior.【F:labs/mcp_stdio.py†L162-L232】【F:tests/test_tcp.py†L175-L188】
- STDIO builder emits the one-time `SYN_SCHEMAS_DIR` deprecation warning ensuring legacy adapters remain discoverable.【F:labs/mcp_stdio.py†L178-L207】【F:tests/test_critic.py†L188-L217】

## Patch Lifecycle — Present
- Preview/apply/rate commands log trace IDs, strict flags, and transports while delegating validation back through Critic to avoid silent drift.【F:labs/patches.py†L47-L156】【F:tests/test_patches.py†L11-L92】

## External Generators — Present
- Gemini/OpenAI integrations honor env-gated live calls, inject redacted Authorization headers, enforce retry/backoff, and normalize payloads before logging.【F:labs/generator/external.py†L82-L840】【F:tests/test_external_generator.py†L43-L365】
- `record_run` emits schema_version, `$schema`, response hashes, and null failures on success, with CLI integration persisting experiments post-review.【F:labs/generator/external.py†L230-L320】【F:tests/test_pipeline.py†L244-L306】

## Logging — Present
- `log_jsonl` underpins generator, critic, patch, and external streams, embedding trace, transport, strict mode, and schema_version metadata.【F:labs/logging.py†L10-L35】【F:labs/agents/generator.py†L118-L195】【F:labs/agents/critic.py†L170-L218】【F:labs/generator/external.py†L230-L320】

## Maintainer Docs — Present
- README, `.example.env`, and process docs now document schema-version targeting controls plus precedence for flag vs env overrides.【F:README.md†L67-L75】【F:.example.env†L18-L21】【F:docs/process.md†L47-L52】
- The spec front matter clearly states v0.3.4 scope and notes future v0.3.5 work to avoid audit ambiguity.【F:docs/labs_spec.md†L1-L20】

## Outstanding Gaps & Divergences
- None observed for this audit scope.
