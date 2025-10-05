# Synesthetic Labs Agents (v0.3.4 audit)

## Generator Agent — Present
- AssetAssembler branches legacy vs enriched payloads, stamps `$schema`, and prunes control mappings before logging experiments with schema_version and transport metadata.【F:labs/generator/assembler.py†L67-L417】【F:labs/agents/generator.py†L71-L199】【F:tests/test_generator_assembler.py†L20-L76】

## Critic Agent — Divergent
- Relaxed mode stops invoking MCP when the validator builder fails yet still returns `ok=True`, allowing persistence despite the spec’s “always validate” rule.【F:labs/agents/critic.py†L130-L205】【F:tests/test_pipeline.py†L197-L207】【F:docs/labs_spec.md†L113-L123】
- Degraded reviews omit the `mcp_response` block, so CLI/external logs cannot record validation results as required.【F:labs/agents/critic.py†L197-L215】【F:tests/test_critic.py†L162-L185】【F:docs/labs_spec.md†L121-L123】

## MCP Resolver — Present
- `resolve_mcp_endpoint` defaults to TCP on unset/invalid values while `build_validator_from_env` provisions STDIO/socket/TCP validators with tests covering fallback and socket failure taxonomy.【F:labs/mcp_stdio.py†L162-L229】【F:tests/test_tcp.py†L175-L188】【F:tests/test_critic.py†L188-L218】

## Patch Lifecycle — Present
- Preview/apply/rate commands log trace, transport, strict flag, and validation context, with tests verifying JSONL persistence under `meta/output/labs/`.【F:labs/patches.py†L47-L156】【F:tests/test_patches.py†L11-L92】

## External Generators — Present
- Gemini/OpenAI integrations enforce live-mode env keys, Authorization header redaction, retry/backoff, size caps, normalization, and `external.jsonl` provenance including schema metadata.【F:labs/generator/external.py†L140-L538】【F:labs/generator/external.py†L600-L678】【F:tests/test_external_generator.py†L27-L279】

## Logging — Present
- `log_jsonl`/`log_external_generation` provide structured JSONL streams used by generator, critic, patches, and external flows, with tests asserting recorded entries.【F:labs/logging.py†L13-L35】【F:labs/agents/generator.py†L102-L199】【F:labs/agents/critic.py†L197-L215】【F:labs/patches.py†L47-L156】【F:labs/generator/external.py†L320-L356】【F:tests/test_logging.py†L10-L20】

## Maintainer Docs — Present
- README, `.example.env`, and process docs document TCP default transport, socket optionality, schema-version targeting precedence, and resolver expectations.【F:README.md†L31-L111】【F:.example.env†L1-L29】【F:docs/process.md†L41-L52】

## Outstanding Gaps & Divergences
- Reinstate MCP validation (or mark failures) in relaxed mode and require populated `mcp_response` data before persisting assets to comply with the v0.3.4 spec.【F:labs/agents/critic.py†L130-L215】【F:labs/cli.py†L160-L199】【F:docs/labs_spec.md†L113-L123】
