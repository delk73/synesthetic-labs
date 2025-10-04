# Synesthetic Labs Agents (Schema Targeting Audit)

## Generator Agent — Missing schema targeting
- CLI lacks the `--schema-version` flag and the env fallback described in the spec, so GeneratorAgent always emits legacy assets.【F:labs/cli.py†L82-L178】
- AssetAssembler hardcodes `$schema` to `meta/schemas/...` and always returns enriched fields, leaving no branch for 0.7.3 vs ≥0.7.4 payloads.【F:labs/generator/assembler.py†L23-L110】
- Generator tests cover logging and provenance only; no schema-version unit matrix exists.【F:tests/test_generator.py†L11-L87】

## Critic Agent — Present
- Enforces required keys, resolves transport defaults, and surfaces strict vs relaxed MCP failures with reason/detail logging.【F:labs/agents/critic.py†L61-L188】【F:tests/test_critic.py†L15-L204】
- Rating stubs and patch lifecycles reuse critic logging metadata for RLHF bookkeeping.【F:labs/agents/critic.py†L190-L218】【F:tests/test_patches.py†L65-L92】

## MCP Resolver — Present
- `resolve_mcp_endpoint` defaults to TCP, while STDIO/Socket builders validate env prerequisites and emit taxonomy-aligned errors.【F:labs/mcp_stdio.py†L162-L232】【F:tests/test_tcp.py†L175-L188】
- Deprecated `SYN_SCHEMAS_DIR` warning fires once in STDIO mode, guarding legacy adapters.【F:labs/mcp_stdio.py†L178-L196】【F:tests/test_critic.py†L204-L217】

## Patch Lifecycle — Present
- Preview/apply/rate paths log trace/mode/transport data and reuse critic validation, preventing silent failures.【F:labs/patches.py†L47-L156】【F:tests/test_patches.py†L11-L92】

## External Generators — Present with Divergences
- Live mode enforces env-gated Authorization headers, retry/backoff, size caps, and normalization with provenance logging.【F:labs/generator/external.py†L166-L780】【F:tests/test_external_generator.py†L117-L365】
- `record_run` omits schema_version and `failure: null` on success, diverging from logging rules; provenance still uses `endpoint` instead of the spec’s `api_endpoint` alias.【F:labs/generator/external.py†L230-L339】【F:docs/labs_spec.md†L113-L133】

## Logging — Present with schema gaps
- Generator, critic, patch, and external logs append structured JSONL under `meta/output/labs/`, but schema_version metadata is missing from external runs.【F:labs/logging.py†L10-L35】【F:labs/generator/external.py†L230-L339】

## Maintainer Docs — Divergent
- README and `.example.env` still reflect v0.3.4 behavior; the spec file has already advanced to v0.3.5 schema-awareness without corresponding code changes.【F:README.md†L19-L104】【F:docs/labs_spec.md†L1-L96】

## Outstanding Gaps & Divergences
- Implement schema_version inputs/branching and update `$schema` URLs to hosted corpus paths.【F:docs/labs_spec.md†L28-L133】【F:labs/generator/assembler.py†L23-L110】
- Extend external logging to emit schema_version plus a null `failure` field when validation passes.【F:docs/labs_spec.md†L113-L133】【F:labs/generator/external.py†L230-L339】
