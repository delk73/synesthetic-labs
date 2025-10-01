# Synesthetic Labs Agents (v0.3.3)

## Generator
- Produces Synesthetic assets from prompts.
- Supports local, Gemini, and OpenAI engines.
- Ensures MCP validation before persistence.

## Critic
- Validates assets in strict/relaxed modes.
- Emits reason/detail on failure.
- Handles TCP (default), STDIO, optional socket.
- Logs reviews and rating stubs.

## MCP Resolver
- Reads MCP_ENDPOINT, MCP_HOST, MCP_PORT, MCP_SOCKET_PATH.
- Falls back to TCP if unset or invalid.

## Patch Lifecycle
- Preview, apply, rate flows.
- Logged under meta/output/labs/patches.jsonl.

## Logging
- Generator, critic, external, and patches all log JSONL to meta/output/labs/.
- Determinism required.

---

_Last reviewed: v0.3.3 (2025-10-01)_
