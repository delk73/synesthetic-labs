# Synesthetic Labs Agents (Schema Targeting Audit)

## Generator Agent — Present with Divergence
- CLI exposes `--schema-version` with env precedence, and tests confirm prompt-to-asset flow across deterministic and external engines.【F:labs/cli.py†L52-L146】【F:tests/test_pipeline.py†L228-L317】
- AssetAssembler branches between `_build_legacy_asset` and enriched output while tagging hosted `$schema` URLs validated by unit tests.【F:labs/generator/assembler.py†L68-L210】【F:tests/test_generator_assembler.py†L1-L87】
- Default schema constant remains 0.7.4 instead of the spec’s 0.7.3 baseline, so runs drift unless operators override via flag/env.【F:labs/generator/assembler.py†L16-L36】【F:docs/labs_spec.md†L61-L76】

## Critic Agent — Present
- Reviewer enforces enriched required fields, resolves transport defaults, and surfaces `mcp_unavailable`/`mcp_error` reasons under strict vs relaxed modes.【F:labs/agents/critic.py†L61-L188】【F:tests/test_critic.py†L15-L204】
- Rating stubs reuse Critic logging metadata to keep RLHF artifacts tied to transports and strict flags.【F:labs/agents/critic.py†L190-L218】【F:tests/test_patches.py†L65-L92】

## MCP Resolver — Present
- `resolve_mcp_endpoint` defaults to TCP, validates stdio/socket prerequisites, and surfaces taxonomy-aligned errors with coverage locking the fallback behavior.【F:labs/mcp_stdio.py†L162-L232】【F:tests/test_tcp.py†L175-L188】
- STDIO builder emits the one-time `SYN_SCHEMAS_DIR` deprecation warning ensuring legacy adapters remain discoverable.【F:labs/mcp_stdio.py†L178-L207】【F:tests/test_critic.py†L188-L217】

## Patch Lifecycle — Present
- Preview/apply/rate commands log trace IDs, strict flags, and transports while delegating validation back through Critic to avoid silent drift.【F:labs/patches.py†L47-L156】【F:tests/test_patches.py†L11-L92】

## External Generators — Present
- Gemini/OpenAI integrations honor env-gated live calls, inject redacted Authorization headers, enforce retry/backoff, and normalize payloads before logging.【F:labs/generator/external.py†L82-L840】【F:tests/test_external_generator.py†L43-L260】
- `record_run` now emits schema_version, `$schema`, response hashes, and null failures on success, with CLI integration persisting experiments post-review.【F:labs/generator/external.py†L230-L320】【F:tests/test_pipeline.py†L244-L306】

## Logging — Present
- `log_jsonl` underpins generator, critic, patch, and external streams, each embedding trace, transport, strict mode, and schema_version metadata.【F:labs/logging.py†L10-L35】【F:labs/agents/generator.py†L118-L195】【F:labs/agents/critic.py†L170-L218】【F:labs/generator/external.py†L230-L320】

## Maintainer Docs — Divergent
- README and `.example.env` enumerate transports and external env vars but omit the new schema-version flag/env guidance required by the spec.【F:README.md†L19-L104】【F:.example.env†L1-L26】
- Process doc references transport resolver discipline yet never mentions schema targeting; spec header already declares v0.3.5 scope, increasing drift risk.【F:docs/process.md†L39-L60】【F:docs/labs_spec.md†L1-L48】

## Outstanding Gaps & Divergences
- Reconcile the 0.7.4 default with the spec’s 0.7.3 baseline (either adjust the constant or update the spec/docs).
- Document schema-version workflows across maintainer materials so operators do not rely on implicit defaults.【F:README.md†L19-L104】【F:.example.env†L1-L26】
