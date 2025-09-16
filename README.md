# Synesthetic Labs

Synesthetic Labs implements the minimal generator → critic loop described in
`docs/labs_spec.md`. The repository is intentionally lightweight and focuses on
being easy to run locally or inside a container.

## Quickstart
1. Install dependencies: `pip install -r requirements.txt`
2. Run the generator: `python -m labs.cli generate "hello world"`
3. Review a proposal: `python -m labs.cli critique path/to/proposal.json`
4. Execute the full test suite: `pytest -q`
5. Mirror CI locally: `./test.sh`

Logs for generator and critic runs are appended to JSONL files inside
`meta/output/`, preserving provenance for audits.
