# Synesthetic Labs Agents (v0.3.4 Audit)

This document captures the audited capabilities of the Labs agents as of the v0.3.4 release cycle.

## Generator Agent — Present
- **AssetAssembler:** Deterministic IDs/timestamps, parameter index collection, and control pruning keep outputs schema-ready. (`labs/generator/assembler.py:78-145`; `tests/test_generator_assembler.py:12-43`)
- **GeneratorAgent:** Emits proposal snapshots with trace/mode/transport/strict data and records MCP-reviewed experiments. (`labs/agents/generator.py:30-145`; `tests/test_generator.py:11-81`)

## Critic Agent — Present
- Validates required fields, resolves transports, and downgrades MCP outages in relaxed mode while logging review payloads. (`labs/agents/critic.py:61-188`; `tests/test_critic.py:25-185`)
- Rating stubs persist trace/mode/transport metadata for RLHF flows. (`labs/agents/critic.py:190-217`; `tests/test_ratings.py:7-30`)

## MCP Resolver — Present
- Defaults to TCP on unset/invalid values and builds stdio/socket/tcp validators with payload caps. (`labs/mcp_stdio.py:162-214`; `tests/test_tcp.py:148-188`)
- STDIO builder forwards the deprecated `SYN_SCHEMAS_DIR` once with a warning. (`labs/mcp_stdio.py:178-188`; `tests/test_critic.py:204-217`)

## Patch Lifecycle — Present
- Preview/apply/rate flows share critic validation, propagate trace/mode/transport/strict fields, and log failures with reason/detail. (`labs/patches.py:47-161`; `tests/test_patches.py:11-114`)

## External Generators — Present with Divergences
- **Live Mode:** Gemini/OpenAI integrations gate on env keys, add Authorization headers, redact logs, and record provenance-rich attempts with retries/backoff per taxonomy. (`labs/generator/external.py:118-515`; `tests/test_external_generator.py:117-263`)
- **CLI Dispatch:** CLI persists only MCP-approved assets and records external runs alongside generator experiments. (`labs/cli.py:115-170`; `tests/test_pipeline.py:229-260`)
- **Normalization:** Canonicalizes sections, rejects unknown keys, and enforces numeric bounds before MCP validation. (`labs/generator/external.py:545-765`; `tests/test_external_generator.py:266-365`)
- **Provenance (Divergent):** `asset.meta_info.provenance` lacks the spec-required `api_version` field and uses `endpoint` in place of `api_endpoint`. (`labs/generator/external.py:980-1019`)
- **external.jsonl schema (Divergent):** Successful entries omit the `failure` key instead of emitting `null` as mandated. (`labs/generator/external.py:309-337`; `docs/labs_spec.md:160-176`)

## Logging — Present
- Generator, critic, patch, and external flows append structured JSONL entries under `meta/output/labs/` with trace/mode/strict/transport metadata and failure taxonomy where applicable. (`labs/logging.py:11-34`; `labs/agents/generator.py:112-188`; `labs/patches.py:47-161`; `labs/generator/external.py:309-355`)

## Maintainer Docs — Present
- Process guide anchors transport provenance expectations to `resolve_mcp_endpoint`. (`docs/process.md:41-45`)

## Outstanding Gaps & Divergences
- Add `api_version` and rename/alias `api_endpoint` in external provenance to match the spec contract. (`labs/generator/external.py:980-1019`; `docs/labs_spec.md:131-142`)
- Ensure `external.jsonl` always includes a `failure` field (null on success) per the documented schema. (`labs/generator/external.py:309-337`; `docs/labs_spec.md:160-176`)
