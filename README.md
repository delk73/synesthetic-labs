# Synesthetic Labs

Synesthetic Labs delivers the v0.1 generator → critic workflow with deterministic Python agents and a container harness that mirrors CI.

## Quickstart
```bash
# Build and test inside Docker
docker build -t synesthetic-labs .
docker run --rm synesthetic-labs

# Convenience wrapper
./test.sh

# Local test suite without Docker
pytest -q
```

Run `python -m labs.cli --help` to explore the CLI. The generator subcommand accepts free-form prompts. The critic subcommand requires a JSON payload and attempts to reach an MCP adapter before running validation.
Note: CriticAgent defaults to MCP schema validation, logs `validation skipped` if the adapter cannot be reached, and records validator responses in the review when validation succeeds. `.env.example` documents MCP_HOST, MCP_PORT, and SYN_* overrides for local setups.

## MCP Adapter
The CLI expects an MCP adapter at `localhost:7000`. When the adapter is unavailable the CriticAgent records `validation skipped` while still emitting a review payload. Provide a stub validator in tests when a sandboxed environment prevents network access.

## Further Reading
- `docs/labs_spec.md` — canonical scope for this release
- `AGENTS.md` — generator and critic provenance
- `meta/prompts/` — canonical prompt set and audit requests
