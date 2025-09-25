# synesthetic-labs Spec

## Purpose

* Deliver a working **generator → MCP validation → logged asset** pipeline.
* Show that Labs can make **schema-valid Synesthetic assets** end-to-end.
* Provide a reproducible baseline for critic, patch lifecycle, RLHF, and external generator extensions.

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

## Scope (v0.3 RLHF)

* Deliver first **RLHF loop**: generator → critic → rating logged.
* Implement **patch rating storage/retrieval**.
* Add **dataset persistence**: rated assets to `meta/dataset/`.
* Provide CLI to **list/filter/export** rated assets.
* Begin **multi-asset orchestration**.

### Canonical Baseline (v0.3)

* Expand modulation set (e.g., LFO on tone frequency).
* Add compound rule bundle (mouse+keyboard → shader+tone).

### Validation (v0.3)

* Ratings only on validated assets.
* Patch diffs schema-checked before rating.

### Logging (v0.3)

* Ratings include patch_id, asset_id, score, critic metadata.
* Dataset persisted under `meta/dataset/` JSONL.

### Tests (v0.3)

* RLHF loop integration.
* Dataset export/filter.
* Determinism checks.

### Exit Criteria (v0.3)

* Ratings retrievable via CLI.
* Dataset persisted.
* Multi-asset orchestration stubbed.
* CI passes.

---

## Scope (v0.4 External Generators)

* Add **Gemini/OpenAI integration** as optional generator sources.
* Define `ExternalGenerator` interface (prompt → JSON asset/patch).
* Wire into Labs pipeline: external candidates still validated by MCP.
* Add retry/backoff + structured error logging for API failures.
* Extend CLI:

  * `generate --engine=gemini "prompt"`
  * `generate --engine=openai "prompt"`.
* Persist provenance (engine name, version, parameters) in generated asset.
* Allow side-by-side runs: deterministic vs external.

### Canonical Baseline (v0.4)

* External generator yields shader+tone+haptic variants beyond stubs.
* Provenance includes engine + API details.

### Validation (v0.4)

* All external outputs must pass MCP validation.
* Failures logged as critic errors.

### Logging (v0.4)

* Provenance extended with `engine: gemini|openai`, `api_version`, `parameters`.
* Logged under `meta/output/labs/external.jsonl`.

### Tests (v0.4)

* Mocked API calls for determinism.
* Fallback to stub generator if external disabled.
* CLI flag parsing.

### Exit Criteria (v0.4)

* External generators pluggable and validated.
* Provenance extended.
* Docs updated.
* Tests pass with mocks.

---

## Backlog (v0.5+)

* Full RLHF dataset curation.
* Multi-agent orchestration with feedback loops.
* Rich modulation/rule libraries.
* Backend persistence and API integration.