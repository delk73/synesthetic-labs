# Synesthetic Labs Agents (v0.3.3 Audit)

## Generator (Present)
- GeneratorAgent logs canonical proposals with assembler provenance and deterministic IDs when seeded (labs/agents/generator.py:37; labs/generator/assembler.py:94; tests/test_generator.py:10)
- Experiment records link validation outcomes and persisted asset paths for traceability (labs/agents/generator.py:78; tests/test_pipeline.py:134)

## Critic (Present)
- Reviews enforce required fields, attempt MCP validation in strict/relaxed modes, and surface transport-specific reason/detail (labs/agents/critic.py:58; labs/agents/critic.py:70; tests/test_critic.py:161)
- Rating stubs append to `meta/output/labs/critic.jsonl` for future RLHF loops (labs/agents/critic.py:170; tests/test_ratings.py:10)

## MCP Resolver (Present)
- Defaults to TCP when `MCP_ENDPOINT` is unset or invalid and builds STDIO/socket validators from env (labs/mcp_stdio.py:134; labs/mcp_stdio.py:171; tests/test_tcp.py:140)
- STDIO branch normalizes deprecated schema paths and warns exactly once (labs/mcp_stdio.py:160; tests/test_critic.py:203)

## Patch Lifecycle (Present)
- Preview, apply, and rate commands log lifecycle records and reuse CriticAgent validation hooks (labs/patches.py:18; labs/patches.py:37; tests/test_patches.py:25)
- Rating stubs propagate into critic logs alongside patch lifecycle entries for RLHF readiness (labs/agents/critic.py:170; tests/test_patches.py:59)

## External Generators (Present)
- Gemini/OpenAI integrations inject provenance, persist MCP-reviewed runs, and expose CLI engines (labs/generator/external.py:115; labs/cli.py:108; tests/test_pipeline.py:211)
- API failures capture attempt traces with structured failure metadata in external logs (labs/generator/external.py:197; tests/test_external_generator.py:52)

## Logging (Divergent)
- Generator, critic, and patch logs omit the spec-required trace_id and mode/transport metadata, blocking compliance (docs/labs_spec.md:206; labs/agents/critic.py:148; labs/patches.py:57)
- Generator experiment records lack structured failure reason/detail despite the logging contract (docs/labs_spec.md:206; labs/agents/generator.py:82)

## Maintainer Docs (Present)
- Maintainer process guidance calls out `resolve_mcp_endpoint` for transport provenance checks (docs/process.md:41; docs/process.md:45)
