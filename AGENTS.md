# Synesthetic Labs Agents (v0.3.3 Audit)

## Generator (Present)
- Deterministic assembler composes canonical sections, prunes dangling controls, and logs JSONL proposals (labs/agents/generator.py:37; labs/generator/assembler.py:66; tests/test_pipeline.py:93)
- Experiment records capture validation outcomes and persisted asset paths for traceability (labs/agents/generator.py:64; tests/test_pipeline.py:120)

## Critic (Present)
- Enforces required fields, strict/relaxed MCP validation paths, and surfaces transport-specific reason/detail (labs/agents/critic.py:46; labs/agents/critic.py:70; tests/test_critic.py:55)
- Records critic reviews and rating stubs into meta/output/labs/critic.jsonl for future RLHF loops (labs/agents/critic.py:148; labs/agents/critic.py:170; tests/test_ratings.py:6)

## MCP Resolver (Divergent)
- Defaults to TCP with unit tests covering unset and invalid MCP_ENDPOINT values (labs/mcp_stdio.py:129; tests/test_tcp.py:163)
- Still forwards the deprecated SYN_SCHEMAS_DIR without emitting the required warning, leaving the cleanup incomplete (docs/labs_spec.md:175; labs/mcp_stdio.py:152)

## Patch Lifecycle (Present)
- Preview, apply, and rate commands log lifecycle records and reuse CriticAgent validation hooks (labs/patches.py:18; labs/patches.py:57; tests/test_patches.py:25)
- Rating stubs propagate into critic logs alongside patch lifecycle entries for RLHF readiness (labs/agents/critic.py:170; tests/test_patches.py:71)

## External Generators (Present)
- Gemini/OpenAI integrations inject provenance with trace IDs and persist MCP-reviewed runs (labs/generator/external.py:115; labs/generator/external.py:168; tests/test_pipeline.py:211)
- API failures capture attempt traces with structured failure metadata in external logs (labs/generator/external.py:197; tests/test_external_generator.py:52)

## Logging (Present)
- log_jsonl underpins generator, critic, patch, and external JSONL sinks with deterministic structure (labs/logging.py:13; labs/agents/critic.py:166; labs/patches.py:82)

## Maintainer Docs (Missing)
- Maintainer process guidance omits the resolve_mcp_endpoint reference required by the spec for future transport provenance work (docs/labs_spec.md:164; docs/process.md:1)
