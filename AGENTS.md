# Synesthetic Labs Agents (v0.3.4 audit)

## Generator Agent — Present
- AssetAssembler defaults to schema 0.7.3, prunes dangling controls, and branches legacy/enriched payloads with hosted `$schema` URLs and provenance wiring.【F:labs/generator/assembler.py†L23-L386】
- GeneratorAgent records schema_version, transport, strict flag, and validation outcomes for experiments, with CLI precedence tests covering flag → env → default ordering.【F:labs/agents/generator.py†L54-L199】【F:tests/test_pipeline.py†L300-L360】

## Critic Agent — Divergent
- Strict mode surfaces `mcp_unavailable`/`mcp_error` taxonomy across transports, but relaxed mode stops invoking MCP when the validator builder fails and still returns `ok`, leading the CLI to persist assets without schema validation.【F:labs/agents/critic.py†L130-L214】【F:tests/test_pipeline.py†L197-L207】
- Resolution should restore MCP invocation (or mark results non-persistable) when running in relaxed mode so the spec mandate to always validate holds.【F:docs/labs_spec.md†L29-L109】

## MCP Resolver — Present
- `resolve_mcp_endpoint` defaults to TCP when unset/invalid and `build_validator_from_env` provisions STDIO, socket, or TCP validators with size caps and deprecation warnings for `SYN_SCHEMAS_DIR`, backed by resolver and socket failure tests.【F:labs/mcp_stdio.py†L162-L229】【F:tests/test_tcp.py†L175-L188】【F:tests/test_critic.py†L188-L217】

## Patch Lifecycle — Present
- Preview/apply/rate flows log trace IDs, transports, strict flags, and reuse critic ratings so lifecycle events stay tied to review context.【F:labs/patches.py†L33-L158】【F:tests/test_patches.py†L11-L92】

## External Generators — Present
- Gemini/OpenAI integrations honor env-configured live mode, inject redacted Authorization headers, enforce retry/backoff and size caps, normalize responses, and append schema-rich runs to `external.jsonl`.【F:labs/generator/external.py†L108-L538】【F:labs/generator/external.py†L311-L372】【F:tests/test_external_generator.py†L27-L279】

## Logging — Present
- `log_jsonl` underpins generator, critic, patch, and external streams, embedding trace/transport/strict metadata with tests asserting persisted JSONL records under `meta/output/labs/`.【F:labs/logging.py†L13-L35】【F:labs/agents/generator.py†L102-L199】【F:tests/test_pipeline.py†L120-L206】

## Maintainer Docs — Present
- README, `.example.env`, and maintainer process docs describe TCP defaults, socket optionality, schema-version controls, and transport resolver expectations aligned with the spec.【F:README.md†L31-L111】【F:.example.env†L1-L29】【F:docs/process.md†L41-L52】

## Outstanding Gaps & Divergences
- Restore MCP invocation (or block persistence) in relaxed mode so assets are not marked `ok` without schema validation.【F:labs/agents/critic.py†L130-L188】【F:labs/cli.py†L160-L189】【F:tests/test_pipeline.py†L197-L207】
