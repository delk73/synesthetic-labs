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

The critic subcommand looks for `MCP_HOST`, `MCP_PORT`, and `SYN_SCHEMAS_DIR`,
falling back to `localhost:7000` and `libs/synesthetic-schemas` when they are
unset. In the default mode, unreachable MCP adapters emit a warning and the
review records `validation_status="skipped"` so local experimentation can
continue. Set `LABS_FAIL_FAST=1` to convert those skips into hard failures and
make the CLI exit non-zero. When validation succeeds, the CriticAgent records
the MCP payload alongside its review. `.env.example` documents the environment
variables.

## Further Reading

* `docs/labs_spec.md` — canonical scope for this release
* `AGENTS.md` — generator and critic provenance
* `meta/prompts/` — canonical prompt set and audit requests
