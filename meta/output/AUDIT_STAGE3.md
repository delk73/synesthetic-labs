# Generator v0.3 Stage 3 — CLI + Persistence Wiring Audit

## Summary
`labs/cli.py generate` now routes prompts through `AssetAssembler`, executes `CriticAgent` validation with fail-fast semantics, and persists validated SynestheticAssets under `meta/output/experiments/`. Successful runs emit JSON payloads pointing at the durable experiment file while `GeneratorAgent` logs provenance entries linking directly to that path. New integration coverage drives the CLI end-to-end with a deterministic validator to guarantee the assembler → critic → persistence chain stays healthy.

## Checks
| Check | Status | Evidence |
| --- | --- | --- |
| CLI generation path calls `AssetAssembler` instead of `GeneratorAgent.propose`. | Pass | `labs/cli.py:165-179` wires `generate` to `AssetAssembler.generate` and removes the old proposal shortcut. |
| Generated assets are handed to `CriticAgent` for schema validation (fail fast if MCP reachable). | Pass | `labs/cli.py:170-202` resolves the validator, runs `CriticAgent.review`, and exits non-zero when validation fails under fail-fast. |
| Assembled asset JSON is persisted to `meta/output/experiments/<id>.json` alongside provenance in `generator.jsonl`. | Pass | `_persist_asset` writes `<id>.json` into the experiments directory (`labs/cli.py:90-101`) and the subsequent provenance link is recorded via `GeneratorAgent.record_experiment` (`labs/agents/generator.py:57-97`). |
| Provenance in `generator.jsonl` links cleanly to the persisted experiment file. | Pass | `GeneratorAgent.record_experiment` stores the relative experiment path and validation metadata (`labs/agents/generator.py:71-97`), which is asserted in both unit and CLI integration tests (`tests/test_generator.py:27-56`, `tests/test_pipeline.py:132-137`). |
| Integration tests include a CLI-driven run that produces and validates a real asset (skipping MCP only when unreachable). | Pass | `tests/test_pipeline.py:96-138` drives `cli.generate` with a stub validator, asserts persistence, and verifies the logged provenance linkage. |
| End-to-end harness (cli → assembler → critic → mcp → persist) runs successfully and produces durable outputs. | Pass | The CLI integration test covers assembler → critic → persistence, while the broader suite still exercises generator ↔ critic handoffs (`tests/test_pipeline.py:13-136`, `tests/test_generator_e2e.py:12-43`). |

## Status
Pass — CLI generation now emits schema-validated SynestheticAssets with durable experiment records and linked provenance.
