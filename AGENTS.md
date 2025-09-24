# Agent Snapshot (v0.2 Audit)

*Audit performed against docs/labs_spec.md v0.2; findings grounded in visible source, tests, and docs.*

## GeneratorAgent
- `propose` delegates to `AssetAssembler.generate` and appends each asset to the generator JSONL sink (labs/agents/generator.py:48; labs/agents/generator.py:60).
- Provenance annotates generator version `v0.1`, preserving deterministic seeds in the logged payload (labs/agents/generator.py:29; labs/agents/generator.py:54).
- `record_experiment` persists validation outcomes with timestamps and optional experiment path references (labs/agents/generator.py:78; labs/agents/generator.py:98).

## AssetAssembler
- Clones component generators and collects a parameter index across shader/tone/haptic sections (labs/generator/assembler.py:50; labs/generator/assembler.py:56).
- Prunes control mappings to parameters present in that index to avoid dangling references (labs/generator/assembler.py:104).
- Emits only shader/tone/haptic/control/meta payloads; modulation and rule bundle stubs remain excluded (labs/generator/assembler.py:62; tests/test_generator_assembler.py:35).

## CriticAgent
- Verifies required asset keys before invoking MCP validation and lazily caches the validator callback (labs/agents/critic.py:33; labs/agents/critic.py:68).
- Supports strict vs relaxed validation via the `LABS_FAIL_FAST` environment toggle, with coverage in tests (labs/agents/critic.py:62; tests/test_critic.py:129).
- Logs review payloads, MCP responses, and validation reasons to `meta/output/labs/critic.jsonl` (labs/agents/critic.py:118; labs/agents/critic.py:130).
- Ratings stubs mandated in v0.2 remain unimplemented (docs/labs_spec.md:74; labs/agents/critic.py:118).

## MCP Bridge & CLI
- `build_validator_from_env` enforces `MCP_ADAPTER_CMD` and forwards optional schema paths to the STDIO adapter (labs/mcp_stdio.py:84; labs/mcp_stdio.py:93).
- CLI `generate`/`critique` flow wraps generator + critic agents and persists validated assets when reviews pass (labs/cli.py:70; tests/test_pipeline.py:92).
- Unix socket transport and patch lifecycle commands are not yet exposed (docs/labs_spec.md:72; labs/cli.py:70).

## Prompt Experiment Harness
- Batch runner loads prompts, reuses the generator/critic pair, and saves per-run assets plus JSONL summaries (labs/experiments/prompt_experiment.py:41; labs/experiments/prompt_experiment.py:68).
- Validator helper still assumes the STDIO adapter path without socket fallback (labs/experiments/prompt_experiment.py:32).

## Logging
- `log_jsonl` ensures log directories exist and writes sorted JSON lines for downstream tooling (labs/logging.py:10).
- Generator and critic agents default to log sinks under `meta/output/labs/` (labs/agents/generator.py:12; labs/agents/critic.py:13).
- Patch/rating log streams required for v0.2 have not been added (docs/labs_spec.md:91; labs/agents/critic.py:118).

## Known gaps vs v0.2 spec
- MCP Unix socket transport absent from runtime and tests (docs/labs_spec.md:72; labs/mcp_stdio.py:1).
- Patch lifecycle preview/apply/rate orchestration and logging missing (docs/labs_spec.md:73; labs/lifecycle/__init__.py:1).
- CriticAgent does not emit ratings stubs (docs/labs_spec.md:74; labs/agents/critic.py:118).
- Modulation and rule bundle stubs are not wired into assembled assets (docs/labs_spec.md:80; labs/generator/assembler.py:62).
- Container image remains root-based without the required hardening (docs/labs_spec.md:75; Dockerfile:1).
