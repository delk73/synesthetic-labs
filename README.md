# Synesthetic Labs

Synesthetic Labs delivers the v0.2 generator → critic workflow with deterministic Python agents, Unix socket MCP transport, and a patch lifecycle stub exercised via the CLI.

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
* `python -m labs.cli preview '{"id": "asset"}' '{"id": "patch", "updates": {...}}'`
* `python -m labs.cli apply '{"id": "asset"}' '{"id": "patch", "updates": {...}}'`
* `python -m labs.cli rate patch-id '{"score": 0.9}' --asset-id asset-id`

Configure the MCP adapter transport using environment variables:

```bash
# STDIO transport (default)
export MCP_ENDPOINT=stdio
export MCP_ADAPTER_CMD="python -m labs.mcp_stub"

# Unix socket transport
export MCP_ENDPOINT=socket
export MCP_SOCKET_PATH="/tmp/synesthetic.sock"
python -m labs.mcp --path "$MCP_SOCKET_PATH"  # launches the bundled adapter once

# TCP transport
export MCP_ENDPOINT=tcp
export MCP_HOST=localhost
export MCP_PORT=8765
# assumes an MCP service is listening on host:port
```

Optional variables such as `SYN_SCHEMAS_DIR`, `LABS_EXPERIMENTS_DIR`, and
`LABS_FAIL_FAST` tune validation and persistence behavior. `LABS_FAIL_FAST`
defaults to strict (`1`) so CLI and experiment runs fail when the MCP adapter
is unavailable; set it to `0`/`false` to log "Validation skipped" and continue
in relaxed mode. The transport helpers enforce a 1 MiB payload cap and
`normalize_resource_path` rejects path traversal in schema or socket
configurations. When the patch lifecycle commands run, the critic logs patch
reviews and rating stubs to `meta/output/labs/critic.jsonl` while the patch
module appends lifecycle events to `meta/output/labs/patches.jsonl`.

```text
+-------------+      STDIO / Socket JSON      +----------------------+      Schema bundle / backend
| Labs (CLI & | ============================> | MCP Adapter (STDIO) | ===========================>
| Experiments)| <============================ |    or socket mode    |
+-------------+                               +----------------------+
```

Generator and critic logs live under `meta/output/labs/`, and validated assets
persist to `meta/output/labs/experiments/` when generation succeeds.

## Further Reading

* `docs/labs_spec.md` — canonical scope for this release
* `AGENTS.md` — generator and critic provenance
* `meta/prompts/` — canonical prompt set and audit requests
