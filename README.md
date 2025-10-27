# Synesthetic Labs v2

## Status

The repository is under reconstruction for the v2 reset. All generator and agent code from the v0.3.6a cycle has been removed. The project now centers on a verified MCP client stack that will drive the next iteration of schema-first tooling.

## Architecture

- `labs/mcp/` provides the client, validation, and transport helpers needed to talk to the Synesthetic MCP registry.
- `labs/transport.py` and `labs/mcp_stdio.py` supply the required transports and remain unchanged from the validated baseline.
- `labs/logging.py` and `labs/core.py` offer shared utilities used by the MCP stack.
- `mcp/` contains the MCP protocol core and is preserved intact.

## What Was Removed

- All generator, agent, lifecycle, experimental, and dataset modules (`labs/generator/`, `labs/agents/`, `labs/experimental/`, etc.).
- Scripts and tests that depended on the removed generator stack, including Azure/Gemini integrations and patch workflows.
- CLI and patch helpers that coupled the MCP client to the deleted modules.

## What Was Kept

- MCP infrastructure directories (`labs/mcp/`, `mcp/`) and their supporting transports.
- Docs, prompts, and archived artifacts for historical reference.
- Lessons learned and environment templates in the repository root.

## Next Steps

1. Follow the cleanup checkpoints documented in `CLEANUP_PLAN.md`.
2. Use `meta/prompts/standup_template.json` when planning the v2 standup work.
3. Extend the MCP test suite as new functionality comes online.

Run `pytest tests/test_mcp*.py tests/test_labs_mcp_modes.py tests/test_socket.py tests/test_tcp.py -v` to verify the preserved MCP surface.
