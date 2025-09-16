# Synesthetic Labs Specification (v0.1)

## Overview
- Provide a deterministic generator → critic loop implemented in Python 3.11+.
- Keep dependencies minimal; only the standard library and `pytest` are required.
- Persist activity to JSONL logs stored under `meta/output/` for auditing.

## Components
- **GeneratorAgent** (`labs/agents/generator.py`)
  - Accepts a prompt string and emits a proposal dictionary with `id`, `timestamp`,
    `prompt`, and `provenance` fields.
  - Uses UUID v4 identifiers and UTC timestamps.
  - Writes each proposal to a JSONL sink using `labs.logging.log_jsonl`.
- **CriticAgent** (`labs/agents/critic.py`)
  - Validates proposal dictionaries by checking the expected keys.
  - Adds `ok` and `issues` fields and records each review via the JSONL sink.
- **CLI** (`labs/cli.py`)
  - Subcommands: `generate` to emit a proposal, `critique` to review a JSON asset.
  - Always prints JSON representations to stdout for easy scripting.

## Testing
- `tests/test_generator.py`: verifies proposal structure and logging.
- `tests/test_critic.py`: verifies review outcomes for valid and invalid assets.
- `tests/test_pipeline.py`: end-to-end generator → critic run.
- All tests must pass with `pytest -q` locally and inside Docker.

## Tooling
- `requirements.txt` lists runtime/test dependencies (`pytest`).
- `Dockerfile` runs `pytest -q` by default for CI parity.
- `docker-compose.yml` exposes a `labs` service that executes the tests.
- `test.sh` builds the container image and runs the compose service.
- CI workflow (`.github/workflows/ci.yml`) installs dependencies and executes `pytest`.

## Documentation & Metadata
- Prompts captured in `meta/prompts/init.json` and `meta/prompts/audit.json` define
  the generator init task and audit format.
- Repository state snapshots are recorded in `meta/output/labs_state.md` and mirrored
  in `AGENTS.md` for quick reference.
- Future improvements and follow-ups live in `meta/backlog.md`.
