# Synesthetic Labs Agents (v0.3.4 Audit)

## Generator (Present)
- AssetAssembler collects parameter indices, prunes dangling control mappings, and injects deterministic provenance for seeded runs `labs/generator/assembler.py:64`; `tests/test_determinism.py:10`
- GeneratorAgent emits proposal snapshots with run metadata and archives experiment summaries for downstream analysis `labs/agents/generator.py:54`; `tests/test_generator.py:24`

## Critic (Present)
- CriticAgent enforces required field coverage, honors `LABS_FAIL_FAST`, and reports transport-specific validation errors `labs/agents/critic.py:63`; `tests/test_critic.py:187`
- Rating events persist to `meta/output/labs/critic.jsonl`, supporting RLHF review loops `labs/agents/critic.py:182`; `tests/test_ratings.py:10`

## MCP Resolver (Present)
- `resolve_mcp_endpoint` defaults to TCP when unset or invalid and scaffolds stdio/socket/tcp transports with payload caps `labs/mcp_stdio.py:134`; `tests/test_tcp.py:163`
- STDIO builder normalizes deprecated `SYN_SCHEMAS_DIR` and issues a one-time compatibility warning `labs/mcp_stdio.py:158`; `tests/test_critic.py:203`

## Patch Lifecycle (Divergent)
- Preview/apply/rate flows reuse CriticAgent validation hooks to guard patch payloads `labs/patches.py:26`; `tests/test_patches.py:25`
- Patch lifecycle logs omit spec-required `trace_id`, strict flag, and transport metadata `docs/labs_spec.md:155`; `labs/patches.py:57`

## External Generators (Divergent)
- Gemini/OpenAI mock integrations capture attempt traces and surface MCP-reviewed results `labs/generator/external.py:115`; `tests/test_external_generator.py:16`
- Live-call obligations (auth headers, env-driven endpoints, schema-normalized defaults, failure taxonomy) are not yet implemented `docs/labs_spec.md:108`; `labs/generator/external.py:275`

## External LIVE Spec (Missing coverage)
- CLI lacks `--seed`, `--temperature`, `--timeout-s`, and `--strict` controls, and `LABS_EXTERNAL_LIVE` gating never wires API keys `docs/labs_spec.md:60`; `labs/cli.py:82`
- Troubleshooting materials and tests do not exercise live-mode error taxonomy or response size guards `docs/labs_spec.md:205`; `tests/test_external_generator.py:52`

## Logging (Divergent)
- Generator, critic, patch, and external logs omit required fields (`trace_id`, mode, transport, strict flag, raw_response hash) `docs/labs_spec.md:155`; `labs/generator/external.py:170`
- Failure reasons fall back to `api_failed`/`validation_failed` instead of enumerated taxonomy codes `docs/labs_spec.md:181`; `labs/generator/external.py:218`

## Maintainer Docs (Present)
- Process guide anchors transport provenance expectations to `resolve_mcp_endpoint` to avoid drift `docs/process.md:41`
