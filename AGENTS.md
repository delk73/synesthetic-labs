# Synesthetic Labs Agents (v0.3.4 audit)

## Generator Agent — Present
- AssetAssembler branches between 0.7.3 legacy and enriched 0.7.4+ payloads, prunes dangling control mappings, stamps `$schema`, and injects provenance with tests covering both schema families.【F:labs/generator/assembler.py†L67-L305】【F:tests/test_generator_assembler.py†L20-L76】
- GeneratorAgent logs schema_version, transport, strict flag, and trace IDs for experiments, mirroring CLI persistence rules and pipeline coverage.【F:labs/agents/generator.py†L67-L199】【F:tests/test_pipeline.py†L102-L188】

## Critic Agent — Present
- Strict mode maps MCP failures to taxonomy-coded `mcp_response` entries and halts persistence; relaxed mode records degraded reviews with `mcp_response.ok=False`, blocking saves and logging warnings as tested.【F:labs/agents/critic.py†L130-L215】【F:labs/cli.py†L201-L240】【F:tests/test_pipeline.py†L197-L233】

## CLI & Environment — Divergent
- CLI preloads `.env` via a bespoke parser while the spec mandates `python-dotenv`, and the dependency list omits the package.【F:docs/labs_spec.md†L75-L79】【F:labs/cli.py†L13-L54】【F:requirements.txt†L1-L3】
- CLI/docs still lean on `LABS_EXTERNAL_LIVE` to toggle live mode despite the spec removing the knob, so warnings/logs contradict requirements.【F:docs/labs_spec.md†L70-L114】【F:labs/cli.py†L51-L53】【F:.example.env†L19-L28】【F:README.md†L24-L170】

## MCP Resolver — Present
- `resolve_mcp_endpoint` defaults to TCP on unset/invalid values and `build_validator_from_env` provisions STDIO/socket/TCP validators with tests covering fallback and socket failure taxonomy.【F:labs/mcp_stdio.py†L162-L229】【F:tests/test_tcp.py†L175-L198】【F:tests/test_critic.py†L188-L218】

## External Generators — Divergent
- Gemini/OpenAI integrations enforce env-configured headers, retry/backoff, size caps, normalization, provenance logging, and MCP validation with extensive tests.【F:labs/generator/external.py†L140-L827】【F:tests/test_external_generator.py†L27-L384】
- Gemini live requests omit `generationConfig.responseMimeType="application/json"`, leaving the structured-output requirement unmet and untested.【F:docs/labs_spec.md†L82-L150】【F:labs/generator/external.py†L1203-L1248】【F:tests/test_external_generator.py†L27-L276】

## Patch Lifecycle — Present
- Preview/apply/rate commands log strict flags, transports, trace IDs, and validation payloads into `meta/output/labs/patches.jsonl`, with tests confirming persistence.【F:labs/patches.py†L47-L156】【F:tests/test_patches.py†L11-L92】

## Logging — Present
- Structured JSONL logging spans generator, critic, external, and patch flows, capturing schema_version, transport, and reason/detail fields with unit coverage.【F:labs/logging.py†L13-L35】【F:labs/agents/generator.py†L97-L199】【F:labs/agents/critic.py†L170-L215】【F:labs/generator/external.py†L320-L356】【F:tests/test_logging.py†L10-L20】

## Documentation — Divergent
- README documents transports, schema targeting, and logging accurately but still references `LABS_EXTERNAL_LIVE` and `load_dotenv`, conflicting with spec expectations.【F:README.md†L24-L170】【F:docs/labs_spec.md†L70-L114】

## Outstanding Gaps & Divergences
- Switch CLI environment preload to `python-dotenv` and add the dependency to comply with spec requirements.【F:docs/labs_spec.md†L75-L79】【F:labs/cli.py†L13-L54】【F:requirements.txt†L1-L3】
- Remove or deprecate `LABS_EXTERNAL_LIVE` across code/docs per spec guidance to avoid contradictory live-mode behaviour.【F:docs/labs_spec.md†L70-L114】【F:labs/cli.py†L51-L53】【F:.example.env†L19-L28】【F:README.md†L24-L170】
- Add `responseMimeType="application/json"` to Gemini live payloads and assert structured-output compliance in tests.【F:docs/labs_spec.md†L82-L150】【F:labs/generator/external.py†L1203-L1248】【F:tests/test_external_generator.py†L27-L276】
