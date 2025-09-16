# Synesthetic Labs

Synesthetic Labs provides a minimal generator → critic workflow for experiments. The
full specification for the v0.1 loop lives in [`docs/labs_spec.md`](docs/labs_spec.md).

## Quickstart
1. Install dependencies: `pip install -r requirements.txt`
2. Explore the CLI: `python -m labs.cli --help`
3. Generate a proposal: `python -m labs.cli generate "hello world"`
4. Critique a proposal from a file: `python -m labs.cli critique proposal.json`
5. Run tests: `pytest -q`
6. Use the container harness: `./test.sh`

Logs from both agents are written to JSONL files under `meta/output/` to
keep each run auditable.
