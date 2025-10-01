# Synesthetic Labs Agents (v0.3.3 Audit)

## Generator (Present)
- Deterministic assembler produces canonical sections and logs JSONL experiments for persisted assets (labs/agents/generator.py:37; labs/agents/generator.py:64; tests/test_pipeline.py:93).
- External engine runs flow through MCP before persistence via the CLI generate command (labs/cli.py:108; labs/cli.py:131; tests/test_pipeline.py:211).

## Critic (Present)
- Enforces required fields and orchestrates MCP validation in both strict and relaxed modes (labs/agents/critic.py:58; labs/agents/critic.py:63; tests/test_pipeline.py:63).
- Logs validation outcomes with reason/detail and records rating stubs for RLHF readiness (labs/agents/critic.py:70; labs/agents/critic.py:170; tests/test_critic.py:55).

## MCP Resolver (Divergent)
- Resolver defaults to TCP with fallback tests covering unset and invalid values (labs/mcp_stdio.py:129; tests/test_tcp.py:163; tests/test_tcp.py:171).
- Still forwards the deprecated SYN_SCHEMAS_DIR knob contrary to the v0.3.3 cleanup requirement (docs/labs_spec.md:184; labs/mcp_stdio.py:152; .env:22).

## Patch Lifecycle (Present)
- Preview, apply, and rate commands log lifecycle records and reuse CriticAgent validation (labs/patches.py:18; labs/patches.py:57; tests/test_patches.py:26).
- Rating stubs are written to critic logs for future RLHF loops (labs/agents/critic.py:170; tests/test_patches.py:49).

## External Generators (Present)
- Gemini/OpenAI integrations inject provenance with trace IDs and record MCP-reviewed runs (labs/generator/external.py:115; labs/generator/external.py:168; tests/test_pipeline.py:211).
- API failures capture attempt traces with structured failure metadata in external logs (labs/generator/external.py:189; tests/test_external_generator.py:52).

## Logging (Present)
- log_jsonl underpins generator, critic, patch, and external JSONL sinks with deterministic structure (labs/logging.py:13; labs/agents/generator.py:61; labs/generator/external.py:200).
