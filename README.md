# Synesthetic Labs

Synesthetic Labs delivers the v0.1 generator → critic workflow with deterministic Python agents and a container harness that mirrors CI.

## Quickstart

```bash
# Build and test inside Docker
docker build -t synesthetic-labs:test .
docker run --rm synesthetic-labs:test

# or use the wrapper
./test.sh

# Local test suite without Docker
pytest -q
```

Run `python -m labs.cli --help` to explore the CLI:

* `python -m labs.cli generate "describe the asset"`
* `python -m labs.cli critique '{"id": "abc", ...}'`

The critic subcommand **requires a running MCP adapter** configured with `MCP_HOST`, `MCP_PORT`, and `SYN_SCHEMAS_DIR`.
If MCP is not reachable, the CLI exits with an error rather than proceeding.
When reachable, the CriticAgent records validator payloads alongside its review.
`.env.example` documents the environment variables.

## Further Reading

* `docs/labs_spec.md` — canonical scope for this release
* `AGENTS.md` — generator and critic provenance
* `meta/prompts/` — canonical prompt set and audit requests
