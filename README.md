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

Configure the STDIO MCP adapter by exporting `MCP_ADAPTER_CMD`. For local
development and CI you can rely on the bundled stub:

```bash
export MCP_ADAPTER_CMD="python -m labs.mcp_stub"
```

Optional variables such as `SYN_SCHEMAS_DIR` and `LABS_EXPERIMENTS_DIR` are
forwarded to the subprocess and persistence layer. `MCP_HOST` and `MCP_PORT`
remain in `.env.example` as compatibility placeholders; MCP validation is
strictly STDIO-based in v0.1. Validation is mandatory: if the adapter command
fails the CLI exits non-zero and records the failure in the review payload. When
validation succeeds, the CriticAgent records the MCP response for provenance.
`.env.example` documents the supported environment variables.

```text
+-------------+      STDIO JSON payload      +----------------------+      Schema bundle / backend
| Labs (CLI & | ============================> | MCP Adapter (STDIO) | ===========================>
| Experiments)| <============================ |    e.g. mcp_stub     |
+-------------+                               +----------------------+
```

Generator and critic logs live under `meta/output/labs/`, and validated assets
persist to `meta/output/labs/experiments/` when generation succeeds. Modulation
and rule bundle generators remain out of scope for this release.

## Further Reading

* `docs/labs_spec.md` — canonical scope for this release
* `AGENTS.md` — generator and critic provenance
* `meta/prompts/` — canonical prompt set and audit requests


