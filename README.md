# Synesthetic Labs

Synesthetic Labs hosts the v0.1 experiment loop for generator → critic workflows that frontload MCP-backed validation. The repo provides small, deterministic Python agents, a CLI, and a container harness that mirrors CI execution.

## Requirements
- Python 3.11+
- Docker (for the canonical harness)

Install development dependencies with `pip install -r requirements.txt` when running locally.

## Quickstart
```bash
# Inspect available commands
python -m labs.cli --help

# Generate a proposal from a prompt stored under meta/prompts/
python -m labs.cli generate init

# Critique a proposal captured as JSON (inline or file path)
python -m labs.cli critique '{"proposal_id": "..."}'
```

The CLI reads prompts from `meta/prompts/`, writes JSONL traces under `meta/output/`, and returns structured JSON to stdout.

## MCP Integration
The CLI defaults to `MCP_HOST=localhost` and `MCP_PORT=7000`. Launch the adapter via `synesthetic-mcp/serve.sh` and keep the backend reachable to enable validation.

When the adapter is offline the critic logs `validation skipped`. If the adapter is reachable but the backend does not expose the required schemas it logs `backend unavailable` and continues without validation.

## Testing
```bash
# Fast local run
pytest -q

# Containerised path-to-green (mirrors CI)
./test.sh
```

## Logging & Artefacts
Structured traces for both agents live in `meta/output/`. Each generator → critic invocation appends JSON lines that capture proposals, critiques, and MCP validation responses for later audit.

## Further Reading
- `docs/labs_spec.md` — authoritative scope for the v0.1 lab
- `AGENTS.md` — generator and critic expectations
- `meta/prompts/` — canonical prompt set used by the CLI and tests
