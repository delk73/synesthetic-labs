# Synesthetic Labs Agents (v0.3.4)

This repository models the Generator and Critic agents defined by the Synesthetic Labs spec.

## Generator Agent
- Branches assets on `schema_version`, emitting the legacy 0.7.3 layout or the enriched ≥0.7.4 structure and injecting the `$schema` URL accordingly.
- Integrates with external engines (Gemini, OpenAI) using structured JSON requests, strict size limits, and provenance logging that records schema version, trace IDs, and failure reasons.
- Normalizes external responses by flagging unknown keys as `bad_response` and out-of-range values as `out_of_range` before assembling final assets.

## Critic Agent
- Invokes MCP validation in both strict and relaxed modes, downgrading outages only when strict mode is disabled.
- Persists generator output solely when the associated `mcp_response.ok` flag is true, capturing MCP availability in the review payload.

## Transport Defaults
- When `MCP_ENDPOINT` is unset or invalid, the CLI resolves to TCP transport, guaranteeing a fallback validation channel.

## Environment Handling
- CLI startup preloads `.env`, merges keys into `os.environ`, and warns when `GEMINI_API_KEY` or `OPENAI_API_KEY` are missing so that external generators run in mock mode by default.
- The legacy `LABS_EXTERNAL_LIVE` knob still exists and should be removed or explicitly deprecated to align with current spec guidance.
