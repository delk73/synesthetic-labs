# Synesthetic Labs Agents (v0.3.4 Audit)

## Generator Agent — Present
- AssetAssembler collects parameter indices, prunes dangling control mappings, and injects deterministic provenance for seeded runs `labs/generator/assembler.py:L50-L102`; `tests/test_generator_assembler.py:L12-L37`
- GeneratorAgent logs proposal snapshots with trace/mode/transport/strict metadata and records MCP-reviewed experiments `labs/agents/generator.py:L48-L145`; `tests/test_generator.py:L11-L81`

## Critic Agent — Present
- Enforces required field coverage, resolves transports, and downgrades MCP outages when relaxed while emitting structured review records `labs/agents/critic.py:L61-L188`; `tests/test_critic.py:L161-L217`
- Rating stubs persist trace/mode/transport metadata for RLHF loops `labs/agents/critic.py:L190-L217`; `tests/test_ratings.py:L7-L33`

## MCP Resolver — Present
- Defaults endpoint selection to TCP on unset/invalid values and validates stdio/socket/tcp payload caps `labs/mcp_stdio.py:L134-L205`; `tests/test_tcp.py:L140-L176`
- STDIO builder normalizes deprecated `SYN_SCHEMAS_DIR` with a single compatibility warning `labs/mcp_stdio.py:L150-L168`; `tests/test_critic.py:L203-L217`

## Patch Lifecycle — Present
- Preview/apply/rate flows share critic validation, propagate trace/mode/transport/strict fields, and log failures with reason/detail `labs/patches.py:L47-L156`; `tests/test_patches.py:L11-L92`

## External Generators — Present with noted gaps
- Gemini/OpenAI live mode gates on env keys, injects Authorization headers, redacts logs, and records provenance-rich attempts `labs/generator/external.py:L118-L515`; `tests/test_external_generator.py:L19-L260`
- CLI dispatch forces MCP-reviewed persistence before writing artifacts `labs/cli.py:L115-L183`; `tests/test_pipeline.py:L200-L244`

## Logging — Present
- Generator, critic, patch, and external flows append structured JSONL entries under `meta/output/labs/` capturing trace, mode, strict, transport, and failure taxonomy `labs/logging.py:L10-L35`; `labs/agents/generator.py:L48-L145`; `labs/agents/critic.py:L61-L217`; `labs/patches.py:L47-L156`; `labs/generator/external.py:L294-L349`

## Maintainer Docs — Present
- Process guide anchors transport provenance expectations to `resolve_mcp_endpoint` to avoid drift `docs/process.md:L41-L45`

## Outstanding Gaps — Divergent / Missing
- Normalization drops unknown keys instead of rejecting them per spec `labs/generator/external.py:L609-L633`; `docs/labs_spec.md:L118-L126`
- Pre-flight numeric bounds (e.g., haptic intensity in [0,1]) are not enforced before MCP validation `labs/generator/external.py:L538-L608`; `docs/labs_spec.md:L148-L153`
- CLI lacks the spec-required `--engine=deterministic` alias `labs/cli.py:L82-L96`; `docs/labs_spec.md:L57-L62`
