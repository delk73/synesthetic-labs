# Synesthetic Labs Agents (v0.3.4 Audit)

This document reflects the audited state of the agents and their capabilities as of the v0.3.4 release cycle.

## Generator Agent — Present
- **AssetAssembler:** Collects parameter indices, prunes dangling control mappings, and injects deterministic provenance for seeded runs. (`labs/generator/assembler.py:L50-L102`; `tests/test_generator_assembler.py:L12-L37`)
- **GeneratorAgent:** Logs proposal snapshots with trace/mode/transport/strict metadata and records MCP-reviewed experiments. (`labs/agents/generator.py:L48-L145`; `tests/test_generator.py:L11-L81`)

## Critic Agent — Present
- Enforces required field coverage, resolves transports, and downgrades MCP outages when relaxed while emitting structured review records. (`labs/agents/critic.py:L61-L188`; `tests/test_critic.py:L161-L217`)
- Rating stubs persist trace/mode/transport metadata for RLHF loops. (`labs/agents/critic.py:L190-L217`; `tests/test_ratings.py:L7-L33`)

## MCP Resolver — Present
- Defaults endpoint selection to TCP on unset/invalid values and validates stdio/socket/tcp payload caps. (`labs/mcp_stdio.py:L134-L205`; `tests/test_tcp.py:L140-L176`)
- STDIO builder normalizes the deprecated `SYN_SCHEMAS_DIR` with a single compatibility warning. (`labs/mcp_stdio.py:L150-L168`; `tests/test_critic.py:L203-L217`)

## Patch Lifecycle — Present
- Preview/apply/rate flows share critic validation, propagate trace/mode/transport/strict fields, and log failures with reason/detail. (`labs/patches.py:L47-L156`; `tests/test_patches.py:L11-L92`)

## External Generators — Present with Gaps
- **Live Mode:** Gemini/OpenAI live mode gates on env keys, injects Authorization headers, redacts logs, and records provenance-rich attempts. (`labs/generator/external.py:L118-L515`; `tests/test_external_generator.py:L19-L260`)
- **CLI Dispatch:** The CLI correctly forces MCP-reviewed persistence before writing artifacts. (`labs/cli.py:L115-L183`; `tests/test_pipeline.py:L200-L244`)
- **Normalization:** The implementation is **Divergent** from the spec. It drops unknown keys instead of rejecting them and is **Missing** pre-flight numeric bounds checking.

## Logging — Present
- Generator, critic, patch, and external flows append structured JSONL entries under `meta/output/labs/` capturing trace, mode, strict, transport, and failure taxonomy. (`labs/logging.py`, `labs/agents/*`, `labs/patches.py`, `labs/generator/external.py`)

## Maintainer Docs — Present
- The process guide anchors transport provenance expectations to `resolve_mcp_endpoint` to avoid future drift. (`docs/process.md`)

## Outstanding Gaps & Divergences
- **Divergent:** Normalization in `labs/generator/external.py` drops unknown keys instead of rejecting them as required by `docs/labs_spec.md`.
- **Missing:** Pre-flight numeric bounds enforcement (e.g., haptic intensity in [0,1]) is not implemented in `labs/generator/external.py` before MCP validation.
- **Missing:** The CLI lacks the spec-required `--engine=deterministic` alias in `labs/cli.py`.
- **Missing:** A unit test for `resolve_mcp_endpoint`'s fallback behavior is missing from the test suite.