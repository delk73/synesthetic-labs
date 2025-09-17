# Agent Snapshot (v0.1 Audit)

## GeneratorAgent
- `propose` enforces non-empty prompts and emits UUID/timestamped payloads with provenance metadata before logging (`labs/agents/generator.py:29`, `labs/logging.py:12`)
- Unit test verifies proposal structure and JSONL persistence for replayability (`tests/test_generator.py:10`)

## CriticAgent
- Validates presence of required generator fields and appends structured reviews to `meta/output/critic.jsonl` (`labs/agents/critic.py:47`, `labs/agents/critic.py:84`)
- Captures MCP validator payloads on success but currently reports `ok=True` when validation is skipped, masking MCP outages (`labs/agents/critic.py:52`, `tests/test_critic.py:45`)

## CLI Integration
- `SocketMCPValidator` relays critique payloads over TCP and surfaces socket failures as `MCPUnavailableError` (`labs/cli.py:19`, `labs/cli.py:33`)
- `_build_validator` requires `MCP_HOST`, `MCP_PORT`, and `SYN_SCHEMAS_DIR`, yet returns `None` when configuration is missing, allowing critiques to proceed without MCP enforcement (`labs/cli.py:64`, `labs/cli.py:109`)

## Test and Pipeline Coverage
- Generator → critic flow, including MCP success responses, is exercised end-to-end via a stub validator (`tests/test_pipeline.py:9`)
- MCP outage handling lacks failing assertions in the test suite and needs expansion after enforcing fail-fast semantics (`tests/test_critic.py:45`)

## Outstanding Gaps
- Enforce fail-fast behavior for skipped MCP validation at the agent and CLI layers (`labs/agents/critic.py:52`, `labs/cli.py:64`)
- Add CLI-focused tests once failure propagation is implemented to prevent regressions (`tests/test_pipeline.py:9`)
