# synesthetic-labs (v0.1)

Synesthetic Labs hosts the v0.1 generator → critic workflow for multimodal asset experiments. The full requirements and design notes live in `docs/labs_spec.md`.

## Quickstart
- Install dependencies: `pip install -r requirements.txt`
- Run the generator → critic CLI: `python -m labs.cli --help`
- Execute tests locally: `pytest`
- Use the container harness (mirrors CI): `./test.sh`

## Project Layout
```
labs/           # Agents, lifecycle, datasets stubs
meta/           # Prompts, backlog, experiment artefacts
tests/          # Pytest coverage for generator, critic, pipeline
```

Logs from runs are appended to JSONL files under `meta/output/` so each experiment remains auditable.
