# synesthetic-labs Spec

## Purpose

* Deliver the first working **generator → MCP validation → logged asset** pipeline.
* Show that Labs can make **schema-valid Synesthetic assets** end-to-end.
* Provide a reproducible baseline for future critic and RLHF extensions.

## Scope (v0.1)

* Implement a **generator agent** that produces a minimal `nested-synesthetic-asset`.
* Assemble Shader, Tone, Haptic sections with canonical defaults.
* Wire through MCP validation (`validate_asset` over STDIO).
* Log validated assets under `meta/output/labs/`.
* Expose CLI:

  ```bash
  python -m labs.cli generate "circle baseline"
  ```

## Non-Scope (deferred v0.2+)

* Critic agent and review flows.
* RLHF/rating loops.
* Patch lifecycle orchestration.
* Dataset building or persistence to backend.

## Component Overview

| Component       | Responsibilities                                    |
| --------------- | --------------------------------------------------- |
| Generator agent | Emit Shader, Tone, Haptic with minimal defaults.    |
| Assembler       | Collect input\_parameters, prune dangling mappings. |
| Labs CLI        | Orchestrate generator → MCP validation → log.       |
| MCP adapter     | Final schema authority.                             |

## Canonical Baseline (v0.1)

* **Shader**: CircleSDF with `u_px`, `u_py`, `u_r`.
* **Tone**: `Tone.Synth` with envelope + detune.
* **Haptic**: Generic device with `intensity`.
* **Controls**: basic mouse.x → shader.u\_px, mouse.y → shader.u\_py.
* **Meta**: `category=multimodal`, `tags=["circle","baseline"]`.

*(All other modulation/rule bundles deferred to v0.2.)*

## Validation

* **Pre-flight**: generator ensures primary sections exist.
* **MCP validation**: assets must pass schema check.
* Fail fast if `LABS_FAIL_FAST=1`.

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
* v0.2 backlog tracked in `meta/backlog.md`.

