# Agent Snapshot (v0.1 Audit)

## GeneratorAgent
- `propose` rejects empty prompts, stamps UUID/ISO timestamps, and appends proposals to JSONL via the shared logger (`labs/agents/generator.py:29`, `labs/logging.py:17`)
- Test suite confirms the logged payload matches the returned proposal for replayability (`tests/test_generator.py:22`)

## CriticAgent
- Verifies required generator fields and emits structured reviews with timestamps and MCP payload echoes (`labs/agents/critic.py:47`, `labs/agents/critic.py:75`)
- Records "validation skipped" when no validator is configured or MCP is unreachable, satisfying the init fallback note but leaving reviews marked successful (`labs/agents/critic.py:55`, `labs/agents/critic.py:72`, `meta/prompts/init.json:22`)
- Captures MCP responses on success, storing them alongside issues for downstream tooling (`labs/agents/critic.py:58`, `tests/test_pipeline.py:19`)

## CLI Integration
- `SocketMCPValidator` wraps TCP calls and raises `MCPUnavailableError` on socket issues so outages can be detected (`labs/cli.py:33`, `labs/cli.py:40`)
- `_build_validator` demands `MCP_HOST`, `MCP_PORT`, and `SYN_SCHEMAS_DIR` but returns `None` when any are missing, letting critiques proceed without validation (`labs/cli.py:64`, `labs/cli.py:80`, `labs/cli.py:109`)
- CLI critique command prints reviews regardless of validation status and never exits non-zero on MCP failures (`labs/cli.py:109`, `labs/agents/critic.py:72`)

## Test and Pipeline Coverage
- Unit tests cover generator logging, critic field checks, and MCP success responses (`tests/test_generator.py:22`, `tests/test_critic.py:22`, `tests/test_pipeline.py:19`)
- Outage handling only asserts a warning message, so fail-fast behavior is untested (`tests/test_critic.py:45`)

## Outstanding Gaps
- Enforce and test fail-fast semantics for skipped MCP validation at both the agent and CLI layers (`labs/agents/critic.py:52`, `labs/cli.py:64`, `docs/labs_spec.md:32`)
- Backfill CLI-focused tests after propagating failures to prevent silent regressions (`labs/cli.py:109`, `tests/test_pipeline.py:19`)
