---
version: v0.3.3
lastReviewed: 2025-10-01
owner: labs-core
---

# Synesthetic Labs Spec

## Purpose

* Deliver a working **generator → MCP validation → logged asset** pipeline.
* Show that Labs can make **schema-valid Synesthetic assets** end-to-end.
* Provide a reproducible baseline for critic, patch lifecycle, external generator integration, and RLHF extensions.

---

## Scope (v0.1)

* **Generator agent** produces a minimal `nested-synesthetic-asset`.
* **Critic agent** coordinates MCP validation and logging.
* Assemble Shader, Tone, Haptic sections with canonical defaults.
* Wire through MCP validation (`validate_asset` over STDIO).
* Log validated assets under `meta/output/labs/`.
* CLI exposes `generate` subcommand.

### Canonical Baseline (v0.1)

* Shader: CircleSDF (`u_px`, `u_py`, `u_r`).
* Tone: `Tone.Synth` with envelope + detune.
* Haptic: Generic device with `intensity`.
* Controls: mouse.x → shader.u_px, mouse.y → shader.u_py (invert).
* Meta: title, description, category=multimodal, complexity=medium, tags.

### Validation (v0.1)

* Pre-flight ensures primary sections exist.
* MCP validation must pass.
* Fail-fast toggle (`LABS_FAIL_FAST`).
* MCP invoked via `MCP_ADAPTER_CMD`; no TCP.

### Logging (v0.1)

* Every run logs: prompt, seed, generated asset, MCP result.

### Tests (v0.1)

* Unit, integration, and end-to-end.
* Determinism enforced.

### Exit Criteria (v0.1)

* Generator produces validated asset.
* Logs under `meta/output/labs/`.
* CLI works inside/outside Docker.
* Tests green.

---

## Scope (v0.2)

* Add **Unix socket transport** for MCP.
* Implement **patch lifecycle orchestration**: preview, apply, rate.
* Expand critic to record **ratings stub**.
* Harden container: non-root user, path traversal guard.
* Align docs/tests to cover STDIO and socket.

### Canonical Baseline (v0.2)

* Add **modulation stubs** (ADSR on tone).
* Add **rule bundle stub** (e.g. radius modulation rule).

### Validation (v0.2)

* Unix socket validation.
* Path normalization + traversal rejection.
* Critic validates patched assets before apply.

### Logging (v0.2)

* Extend logs with patch ops + rating stubs.

### Tests (v0.2)

* Socket round-trip, traversal rejection, patch lifecycle integration, rating stub logging, container non-root.

### Exit Criteria (v0.2)

* Socket transport functional.
* Patch lifecycle stubbed and logged.
* Critic logs ratings.
* Container hardened.
* Docs updated.

---

## Scope (v0.2-TCP)

* Add **TCP transport** for MCP.
* Support `MCP_HOST`/`MCP_PORT` in env.
* Implement `TcpMCPValidator` with 1 MiB cap.
* Update CLI dispatch (`MCP_ENDPOINT=tcp`).
* Add TCP tests: round-trip, oversize payload, error handling.
* Critic emits structured reason/detail on TCP failures.
* Docs updated with TCP workflows.

### Exit Criteria (v0.2-TCP)

* TCP validator and tests pass.
* Docs and `.env` accurate.
* Critic structured error fields present.

---

## Scope (v0.3 External Generators)

* Add **Gemini/OpenAI integration** as optional generator sources (`labs/generator/external.py`).
* Define an `ExternalGenerator` interface with prompt → JSON asset/patch parsing plus provenance injection.
* Wire into Labs pipeline so external candidates still run through MCP + critic review (`labs/cli.py`).
* Add retry/backoff + structured error logging for API outages (`ExternalGenerationError`).
* Default to mock mode for CI; enable live calls via `LABS_EXTERNAL_LIVE=1` and optional transport overrides.
* Extend CLI:

  * `generate --engine=gemini "prompt"`
  * `generate --engine=openai "prompt"`

* Persist provenance (engine name, version, parameters) in generated asset.
* Allow side-by-side runs: deterministic vs external.

### Canonical Baseline (v0.3)

* External generator yields shader+tone+haptic variants beyond stubs.
* Provenance includes engine + API details.

### Validation (v0.3)

* All external outputs must pass MCP validation before persistence.
* Validator outages still honour fail-fast vs relaxed modes, mirroring local runs.
* Critic and external logs capture structured `validation_failed` reasons on failure.

### Logging (v0.3)

* Provenance extended with `engine: gemini|openai`, `api_version`, `parameters`, and per-run `trace_id`.
* External runs logged under `meta/output/labs/external.jsonl` with prompt, raw API response, normalised asset, MCP result, critic review, and failure metadata when applicable.
* `log_external_generation` helper appends JSONL entries alongside existing generator/critic streams.

### Tests (v0.3)

* Mocked API calls for determinism (`tests/test_external_generator.py`).
* CLI flag parsing + end-to-end validation for `--engine` (`tests/test_pipeline.py`).
* Logging helper writes structured external entries (`tests/test_logging.py`).

### Exit Criteria (v0.3)

* External generators pluggable, retried on failure, and validated via MCP.
* Provenance extended and persisted assets include engine/API metadata.
* External runs recorded in `meta/output/labs/external.jsonl`.
* CLI flag usage and documentation updated to cover external engines.
* Tests pass with mocks and no live API requirements.

---

## Scope (v0.3.1 Hardening)

* Make TCP the **default MCP transport** for Labs.
* Clarify that **Unix socket transport** is optional and only tested if supported by the environment (`LABS_SOCKET_TESTS`).
* Enforce MCP validation calls in all modes — relaxed mode may downgrade failures to warnings, but never skip validation.
* Prune unused backend variables from `.env` and documentation to reduce drift.
* Document socket optionality in README and CI guidance and remove legacy backend environment knobs from samples.

### Exit Criteria (v0.3.1)

* TCP transport remains primary and passes tests in CI.
* Socket tests are explicitly marked optional; not counted as failures if skipped.
* MCP validation is always invoked, with relaxed mode changing severity not behavior.
* `.env` and README accurately reflect required vars only.
* Deprecated backend environment knobs are removed or clearly marked as such in docs and samples.

---

## Scope (v0.3.3 Spec Alignment)

* **Test Coverage Gaps:** Add explicit tests for resolve_mcp_endpoint fallback and critic socket failure handling.
* **Docs Cleanup:** Update docs/labs_spec.md and README to reference resolver fallback.
* **Environment Cleanup:** Remove unused SYN_SCHEMAS_DIR from .example.env and docs.
* **AGENTS.md Refresh:** Update with current agent roles.

### Exit Criteria

* Tests cover resolve_mcp_endpoint fallback and critic socket failure.
* README and docs reference resolver fallback.
* .env pruned of unused vars.
* AGENTS.md up-to-date.
* CI passes.

---

## Scope (v0.4 RLHF)

* Deliver first **RLHF loop**: generator → critic → rating logged.
* Implement **patch rating storage/retrieval**.
* Add **dataset persistence**: rated assets to `meta/dataset/`.
* Provide CLI to **list/filter/export** rated assets.
* Begin **multi-asset orchestration**.

### Canonical Baseline (v0.4)

* Expand modulation set (e.g., LFO on tone frequency).
* Add compound rule bundle (mouse+keyboard → shader+tone).

### Validation (v0.4)

* Ratings only on validated assets.
* Patch diffs schema-checked before rating.

### Logging (v0.4)

* Ratings include patch_id, asset_id, score, critic metadata.
* Dataset persisted under `meta/dataset/` JSONL.

### Tests (v0.4)

* RLHF loop integration.
* Dataset export/filter.
* Determinism checks.

### Exit Criteria (v0.4)

* Ratings retrievable via CLI.
* Dataset persisted.
* Multi-asset orchestration stubbed.
* CI passes.

---

## Backlog (v0.5+)

* Full RLHF dataset curation.
* Multi-agent orchestration with feedback loops.
* Rich modulation/rule libraries.
* Backend persistence and API integration.
