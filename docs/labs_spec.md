# synesthetic-labs Spec

## Purpose

* Deliver the first working **generator → MCP validation → logged asset** pipeline.
* Show that Labs can make **schema-valid Synesthetic assets** end-to-end.
* Provide a reproducible baseline for future critic and RLHF extensions.

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

## Non-Scope (future work)

* RLHF/rating loops.
* Patch lifecycle orchestration.
* Dataset building or persistence to backend.

## Component Overview

| Component       | Responsibilities                                    |
| --------------- | --------------------------------------------------- |
| Generator agent | Emit Shader, Tone, Haptic with minimal defaults.    |
| Critic agent    | Review assets, invoke MCP validation, log outcomes. |
| Assembler       | Collect input\_parameters, prune dangling mappings. |
| Labs CLI        | Orchestrate generator → MCP validation → log.       |
| MCP adapter     | Final schema authority.                             |

## Canonical Baseline (v0.1)

* **Shader**: CircleSDF with `u_px`, `u_py`, `u_r`.
* **Tone**: `Tone.Synth` with envelope + detune.
* **Haptic**: Generic device with `intensity`.
* **Controls**: basic mouse.x → shader.u\_px, mouse.y → shader.u\_py.
* **Meta**: `category=multimodal`, `tags=["circle","baseline"]`.

*(All other modulation/rule bundles are deferred to later releases.)*

## Validation

* **Pre-flight**: generator ensures primary sections exist.
* **MCP validation**: assets must pass schema check.
* **Fail-fast toggle** (`LABS_FAIL_FAST`, default strict): values `1/true/on` enforce immediate failures; `0/false/off` logs "Validation skipped" and allows relaxed runs.
* Provide the MCP STDIO command via `MCP_ADAPTER_CMD`; TCP fallbacks are not permitted.
* `python -m labs.mcp_stub` offers a local no-op adapter for smoke tests.

## Logging

* Every run logs: prompt, seed, generated asset, MCP result.
* Stored as JSONL under `meta/output/labs/`.

## Tests

* Unit: generator outputs syntactically valid sections.
* Integration: generator → assembler → MCP validation.
* E2E: CLI run produces an output file under `meta/output/labs/`.
* Determinism: fixed seed yields identical JSON.

## Constraints

* No schema authority inside Labs.
* MCP is required for validation.
* Container and local runs must behave identically.

## Exit Criteria

* Generator produces end-to-end validated asset.
* Logs written under `meta/output/labs/`.
* CLI works inside/outside Docker.
* Tests pass in CI.
* Backlog items tracked in `meta/backlog.md`.

## Documented Divergences

* None for v0.1.
