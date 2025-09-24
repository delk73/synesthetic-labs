# synesthetic-labs Spec

## Purpose

* Deliver a working **generator → MCP validation → logged asset** pipeline.
* Show that Labs can make **schema-valid Synesthetic assets** end-to-end.
* Provide a reproducible baseline for future critic, patch lifecycle, and RLHF extensions.

---

## Scope (v0.1)

* Implement a **generator agent** that produces a minimal `nested-synesthetic-asset`.
* Deliver a **critic agent** that coordinates MCP validation and logging.
* Assemble Shader, Tone, Haptic sections with canonical defaults.
* Wire through MCP validation (`validate_asset` over STDIO).
* Log validated assets under `meta/output/labs/`.
* Expose CLI:

  ```bash
  python -m labs.cli generate "circle baseline"
  ```

## Canonical Baseline (v0.1)

* **Shader**: CircleSDF with `u_px`, `u_py`, `u_r`.
* **Tone**: `Tone.Synth` with envelope + detune.
* **Haptic**: Generic device with `intensity`.
* **Controls**:

  * `mouse.x` → `shader.u_px` (`mode=absolute`, `curve=linear`, `range=[-1.0, 1.0]`).
  * `mouse.y` → `shader.u_py` (`mode=absolute`, `curve=linear`, `range=[-1.0, 1.0]`, `invert=true`).
* **Meta**:

  * `title`: "Circle Interaction Baseline".
  * `description`: "Canonical multimodal baseline featuring a CircleSDF shader, Tone.Synth audio bed, and haptic pulse cues.".
  * `category`: `multimodal`.
  * `complexity`: `medium`.
  * `tags`: \["circle", "baseline"].

## Validation (v0.1)

* **Pre-flight**: generator ensures primary sections exist.
* **MCP validation**: assets must pass schema check.
* **Fail-fast toggle** (`LABS_FAIL_FAST`, default strict).
* MCP invoked via `MCP_ADAPTER_CMD`; TCP fallbacks not permitted.
* `python -m labs.mcp_stub` provides no-op adapter for smoke tests.

## Logging (v0.1)

* Every run logs: prompt, seed, generated asset, MCP result.
* Stored as JSONL under `meta/output/labs/`.

## Tests (v0.1)

* Unit: generator outputs syntactically valid sections.
* Integration: generator → assembler → MCP validation.
* E2E: CLI run produces output under `meta/output/labs/`.
* Determinism: fixed seed yields identical JSON.

## Exit Criteria (v0.1)

* Generator produces end-to-end validated asset.
* Logs written under `meta/output/labs/`.
* CLI works inside/outside Docker.
* Tests pass in CI.

---

## Scope (v0.2)

* Add **Unix socket transport** for MCP alongside STDIO.
* Implement **patch lifecycle orchestration**: preview, apply, rate.
* Expand critic agent to record **ratings stub**.
* Harden container execution: **non-root user** and path traversal guard.
* Align documentation and tests to cover both STDIO and socket modes.

## Canonical Baseline (v0.2)

* Add **modulation stubs** (e.g., ADSR curve on tone).
* Add **rule bundle stub** (e.g., radius modulation rule).

## Validation (v0.2)

* Add **Unix socket transport validation** (`MCP_ENDPOINT=socket`).
* Enforce **path normalization and traversal rejection** on schemas/examples.
* Extend critic to validate **patched assets** before apply.

## Logging (v0.2)

* Extend logs with **patch operations** and **rating stubs**.
* Maintain JSONL under `meta/output/labs/`.

## Tests (v0.2)

* Socket transport: client/server round-trip with size caps.
* Path traversal rejection.
* Patch preview/apply integration.
* Rating stub logging.
* Container runs as non-root.

## Exit Criteria (v0.2)

* MCP socket transport functional and tested.
* Patch lifecycle (preview, apply, rate) stubbed and logged.
* Critic agent records ratings stub.
* Container hardened to non-root with no regressions.
* Path traversal rejection enforced and tested.
* Docs reflect STDIO + socket workflows.

---

## Scope (v0.3)

* Deliver first **RLHF loop** with critic-agent ratings.
* Implement **patch rating storage** and retrieval.
* Add **dataset persistence**: append rated assets into training corpus.
* Provide CLI to **list, filter, and export** rated assets.
* Begin support for **multi-asset orchestration**.

## Canonical Baseline (v0.3)

* Expand **modulation set** (e.g., LFO modulation of tone frequency).
* Add **rule bundle** for compound controls (e.g., mouse + keyboard → shader + tone).

## Validation (v0.3)

* Ratings must be attached to **validated assets only**.
* Validation extended to ensure **patch diffs** are schema-safe before rating.

## Logging (v0.3)

* Ratings logged with: `patch_id`, `asset_id`, `rating`, `critic_metadata`.
* Dataset persisted under `meta/dataset/` as JSONL.

## Tests (v0.3)

* RLHF loop integration: generator → critic → rating stored.
* Dataset export and filtering.
* Determinism: re-run with fixed seed + rating yields identical JSONL export.

## Exit Criteria (v0.3)

* Ratings stored and retrievable via CLI.
* Dataset persisted under `meta/dataset/`.
* Multi-asset orchestration stub functional.
* Tests pass in CI.

---

## Backlog (v0.4+)

* Full RLHF dataset curation.
* Multi-agent orchestration with feedback loops.
* Rich modulation/rule libraries.
* Backend persistence and API integration.