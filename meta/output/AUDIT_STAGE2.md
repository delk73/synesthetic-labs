# Generator v0.2 Stage 2 — Assembler + CLI Wiring Audit

## Summary
Asset-level wiring inside `AssetAssembler` remains internally consistent: shader, tone, and haptic input parameters propagate cleanly into controls, modulators, and rule effects with protective pruning. However, the CLI and experiment surfaces still rely on the legacy `GeneratorAgent` proposal flow, so no assembled assets are produced, validated, or persisted. As a result, the end-to-end objective of delivering complete SynestheticAssets through `labs/cli.py generate` and into `meta/output/experiments/` is currently unmet.

## Checks
| Check | Status | Evidence |
| --- | --- | --- |
| Assembler gathers `input_parameters` from shader/tone/haptic and injects them into controls and modulations. | Pass | `AssetAssembler.generate` collects parameters and prunes dependent components before emitting the asset (`labs/generator/assembler.py:59`-`92`). |
| ControlGenerator references only valid parameters from other sections. | Pass | Baseline mappings target shader/tone parameters and survive assembler pruning (`labs/generator/control.py:8`-`33`, `labs/generator/assembler.py:107`-`116`). |
| ModulationGenerator produces targets that exist in shader/tone/haptic. | Pass | Modulator definitions reference declared parameters and are filtered by `_prune_modulators` (`labs/generator/modulation.py:8`-`35`, `labs/generator/assembler.py:117`-`126`). |
| RuleBundleGenerator effects reference valid parameters. | Pass | Rule effects align with parameter index; invalid targets would be dropped by `_prune_rule_bundle` (`labs/generator/rule_bundle.py:8`-`60`, `labs/generator/assembler.py:128`-`148`). |
| `labs/cli.py generate` calls `AssetAssembler` and produces a complete SynestheticAsset, not just a log entry. | Fail | CLI `generate` still instantiates `GeneratorAgent` and returns the bare proposal envelope (`labs/cli.py:135`-`139`), while `GeneratorAgent.propose` omits component data (`labs/agents/generator.py:41`-`53`). |
| Final asset is persisted to `meta/output/experiments/<id>.json` alongside `generator.jsonl` provenance. | Fail | No persistence path writes assembled assets; the runtime only appends proposal metadata to `meta/output/generator.jsonl` (`labs/agents/generator.py:52`-`53`) and lacks any `meta/output/experiments/` handling. |
| Final asset passes MCP schema validation when run through CriticAgent (skip if MCP unreachable). | Skipped | Validation remains dependent on optional environment configuration; `tests/test_generator_assembler.py:70`-`75` skips when MCP settings are absent, and CLI never reaches MCP with an assembled asset. |
| Integration tests assert no dangling references (e.g., invalid shader param). | Pass | Unit tests enforce cross-component references for assembled payloads (`tests/test_generator_assembler.py:46`-`67`). |
| E2E harness (generator → assembler → critic → MCP) runs successfully and logs outputs. | Pass (stubbed MCP) | End-to-end test drives `AssetAssembler` through `CriticAgent` using a stub validator and verifies JSON/JSONL persistence (`tests/test_generator_e2e.py:12`-`43`). |

## Findings
- CLI generation path must replace `GeneratorAgent.propose` with `AssetAssembler.generate` (and associated logging) to emit full SynestheticAssets.
- Persistence strategy for assembled assets is missing; introduce an experiments directory writer that stores `<id>.json` and updates provenance in parallel with JSONL logging.
- MCP validation is only opportunistically exercised; once assembled assets flow through the CLI, wire the `CriticAgent` review step (with fail-fast semantics) so schema validation is enforced when reachable.

## Recommended Next Steps
1. Update `labs/cli.py` and any experiment runners to invoke `AssetAssembler` and hand the result to `CriticAgent` before printing/logging.
2. Implement persistence for assembled assets under `meta/output/experiments/` (including provenance linkage) and backfill tests covering file creation.
3. Provide deterministic mocks or fixtures for MCP validation so the CLI path is verifiable under test and fail-fast semantics can be enforced.

## Status
Fail — Assembler internals are sound, but CLI + persistence gaps prevent end-to-end delivery of schema-validated Synesthetic assets.
