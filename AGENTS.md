# Synesthetic Labs Agents (v0.3.4 Audit)

## Generator (Present)
- AssetAssembler collects parameter indices, prunes dangling control mappings, and injects deterministic provenance for seeded runs `labs/generator/assembler.py:64`; `tests/test_determinism.py:10`
- GeneratorAgent logs proposals and persists experiment summaries, though metadata upgrades remain pending elsewhere `labs/agents/generator.py:54`; `tests/test_generator.py:24`

## Critic (Present)
- Reviews gate required fields, respect LABS_FAIL_FAST, and emit transport-specific validation errors including socket fallback detail `labs/agents/critic.py:63`; `tests/test_critic.py:187`
- Rating stubs append to `meta/output/labs/critic.jsonl` for RLHF loops `labs/agents/critic.py:182`; `tests/test_ratings.py:10`

## MCP Resolver (Present)
- `resolve_mcp_endpoint` falls back to TCP on unset/invalid values and builders cover stdio/socket/tcp transports with payload caps `labs/mcp_stdio.py:134`; `tests/test_tcp.py:163`
- STDIO branch normalizes deprecated `SYN_SCHEMAS_DIR` and warns once as required `labs/mcp_stdio.py:158`; `tests/test_critic.py:203`

## Patch Lifecycle (Divergent)
- Preview/apply/rate commands log lifecycle records and reuse CriticAgent validation hooks `labs/patches.py:26`; `tests/test_patches.py:25`
- Logs lack trace_id, strict flag, and transport metadata mandated by the spec `docs/labs_spec.md:155`; `labs/patches.py:57`

## External Generators (Divergent)
- Gemini/OpenAI mock integrations capture attempt traces and MCP-reviewed runs `labs/generator/external.py:115`; `tests/test_external_generator.py:16`
- Live-call requirements (Authorization headers, env-driven endpoints, schema-normalized defaults, failure taxonomy) remain unimplemented `docs/labs_spec.md:108`; `labs/generator/external.py:275`

## External LIVE Spec (Missing)
- CLI lacks `--seed/--temperature/--timeout-s/--strict` controls and LABS_EXTERNAL_LIVE gating does not wire API keys `docs/labs_spec.md:60`; `labs/cli.py:82`; `.example.env:1`
- No troubleshooting doc or tests cover live-mode error taxonomy and size guards `docs/labs_spec.md:205`; `tests/test_external_generator.py:52`

## Logging (Missing)
- Generator, critic, patch, and external logs omit spec-required trace_id, mode, transport, strict flag, and raw_response hash fields `docs/labs_spec.md:155`; `labs/generator/external.py:170`
- Failure reasons fall back to `api_failed`/`validation_failed` instead of the enumerated taxonomy for RLHF readiness `docs/labs_spec.md:181`; `labs/generator/external.py:218`

## Maintainer Docs (Present)
- Process guide anchors transport provenance expectations to `resolve_mcp_endpoint` to prevent drift `docs/process.md:41`
