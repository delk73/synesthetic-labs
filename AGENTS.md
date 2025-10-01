# Synesthetic Labs Agents (v0.3.3 Audit)

## Generator (Present)
- Deterministic assembler composes canonical sections, prunes dangling controls, and logs JSONL proposals (labs/agents/generator.py:37; labs/generator/assembler.py:64; tests/test_pipeline.py:15)
- Experiment records capture validation outcomes and persisted asset paths for traceability (labs/agents/generator.py:64; tests/test_pipeline.py:93)

## Critic (Present)
- Required field enforcement and strict/relaxed MCP handling surface transport-specific reason/detail (labs/agents/critic.py:63; labs/agents/critic.py:70; tests/test_critic.py:23)
- Reviews and rating stubs append to meta/output/labs/critic.jsonl enabling future RLHF loops (labs/agents/critic.py:148; labs/agents/critic.py:180; tests/test_ratings.py:10)

## MCP Resolver (Present)
- Defaults to TCP when MCP_ENDPOINT is unset or invalid with resolver fallback tests in place (labs/mcp_stdio.py:134; tests/test_tcp.py:163)
- STDIO branch normalizes SYN_SCHEMAS_DIR and issues the deprecation warning on first forward (labs/mcp_stdio.py:160; docs/labs_spec.md:175)

## Patch Lifecycle (Present)
- Preview, apply, and rate commands log lifecycle records and reuse CriticAgent validation hooks (labs/patches.py:18; labs/patches.py:37; tests/test_patches.py:25)
- Rating stubs propagate into critic logs alongside patch lifecycle entries for RLHF readiness (labs/agents/critic.py:180; tests/test_patches.py:54)

## External Generators (Present)
- Gemini/OpenAI integrations inject provenance, persist MCP-reviewed runs, and expose CLI engines (labs/generator/external.py:115; labs/cli.py:191; tests/test_pipeline.py:191)
- API failures capture attempt traces with structured failure metadata in external logs (labs/generator/external.py:214; tests/test_external_generator.py:52)

## Logging (Present)
- log_jsonl underpins generator, critic, patch, and external JSONL sinks with deterministic structure (labs/logging.py:13; tests/test_logging.py:10)

## Maintainer Docs (Present)
- Maintainer process guidance calls out resolve_mcp_endpoint for transport provenance checks (docs/process.md:41; docs/process.md:45)
