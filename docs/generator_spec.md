# Generator v0.2 — Component + Wiring Design (Revised)

## Purpose
Upgrade Labs Generator from proposal stubs to full, schema-valid Synesthetic assets. Each primary section (shader, tone, haptic) is produced by a dedicated component generator. Secondary generators (controls, modulations) decorate the exposed parameter surfaces. A wiring step enforces that all cross-references resolve. Output is validated against the SSOT schema via MCP and logged with provenance.

## Architecture
- **Primary Component Generators**
  - **ShaderGenerator**: GLSL fragment/vertex, uniforms, input_parameters (e.g., `u_px`, `u_py`, `u_r`).
  - **ToneGenerator**: `Tone.Synth` baseline with input_parameters + optional effects/parts/patterns.
  - **HapticGenerator**: generic device with `intensity` and `frequency` input_parameters.

- **Secondary Generators (depend on primary parameter surfaces)**
  - **ControlGenerator**: maps gestures (mouse/keys/wheel) only to parameters declared by Shader/Tone/Haptic.
  - **ModulationGenerator**: LFO/envelope-style modulations (`triangle`, `sine`, additive) targeting valid parameters.

- **RuleBundleGenerator**
  - Default grid mapping that triggers audio notes, haptic pulses, and small visual nudges. Targets must exist.

- **MetaGenerator**
  - Descriptions, tags, and complexity; no behavioral semantics.

## Wiring Step (Assembler)
1. Collect all declared `input_parameters` from Shader/Tone/Haptic into an index (e.g., `{ "shader.u_r", "tone.detune", "haptic.intensity" }`).
2. Controls: retain only mappings whose `parameter` exists in the index; drop or rewrite dangling mappings.
3. Modulations: retain only entries whose `target` exists; drop or rewrite dangling targets.
4. RuleBundle: ensure each effect `target` exists; drop or rewrite invalid targets.
5. Apply provenance `{uuid, timestamp, prompt, seed, generator_version}`.

## Validation (Two Stages)
1. **Local pre-flight** (fast, deterministic):
   - Non-empty primary sections (shader/tone/haptic).
   - Ranges/units sanity (min < default < max, valid steps).
   - Cross-section checks (no dangling targets in controls/modulations/rules).
2. **Authoritative MCP validation** (SSOT schema):
   - Send assembled asset to MCP; accept/reject based on schema.
   - In strict mode (`LABS_FAIL_FAST=1`), unreachable MCP or schema errors fail the run.

## Flow
1. Primary generators emit Shader, Tone, Haptic with canonical defaults.
2. Secondary generators propose Controls and Modulations against discovered parameter surfaces.
3. RuleBundle generator proposes default grid mapping.
4. Assembler wires and prunes to ensure all references resolve.
5. Validate (pre-flight → MCP).
6. Persist/log with provenance to `meta/output/` (and optionally persist via MCP when implemented).

## Canonical Baseline (v0.2)
- **Shader**: CircleSDF with `u_px`, `u_py`, `u_r` + `u_time`, `u_resolution`.
- **Tone**: Canonical `Tone.Synth` (volume, detune, envelope, portamento) + single Reverb effect.
- **Haptic**: Generic device with `intensity` and `frequency`.
- **Controls**:
  - `mouse.x` → `shader.u_px` (linear)
  - `mouse.y` → `shader.u_py` (linear, inverted sensitivity)
  - `Shift+mouse` → `tone.detune`
  - `Ctrl+Alt+mouse` → `haptic.intensity`
  - `Ctrl+right+mouse` → `haptic.frequency`
- **Modulations**:
  - Triangle LFO → `shader.u_r` (radius pulse)
  - Triangle LFO → `tone.detune` (subtle drift)
  - Sine LFO → `haptic.intensity` (rhythmic pulse)
- **RuleBundle**: Grid press triggers `audio.poly.trigger`, sets `haptic.intensity`, and adds `shader.u_r` nudge.
- **Meta**: `category=multimodal`, `complexity=medium`, tags such as `[circle, interactive, audio, haptic]`.

## Determinism & Randomization
- Generator accepts an optional `seed`. When provided, output must be bit-for-bit identical across runs.
- Without a seed, allow bounded variation (e.g., small detune/reverb defaults) but keep ranges schema-safe.
- Provenance must always record `{seed}` (or `null` when absent).

## Testing Strategy
- **Unit (per generator)**:
  - Shader/Tone/Haptic: section conforms to schema; declares coherent `input_parameters` (min/default/max/step).
  - Controls/Modulations: generated entries are syntactically valid (no semantics yet).
- **Cross-Section Tests**:
  - Every `control.parameter` exists in `{shader.*, tone.*, haptic.*}`.
  - Every `modulations.target` exists in `{shader.*, tone.*, haptic.*}`.
  - Every `rule_bundle.effects[].target` exists in `{shader.*, tone.*, haptic.*}`.
- **Integration**:
  - Assembler prunes/rewrites dangling references; result has zero orphans.
- **E2E**:
  - Generator → Critic → MCP validation → JSONL export under `meta/output/`.
  - Optional: persistence via MCP route once implemented.
- **Determinism**:
  - Fixed seed → identical JSON (byte-for-byte).

## Operational Modes
- Default: relaxed mode; MCP outages mark validation as `skipped` but still log asset.
- Strict: set `LABS_FAIL_FAST=1`; MCP outages or schema errors → non-zero exit and `ok=false` review.

## Open Decisions (track in backlog)
- Baseline family: stick to CircleSDF minimal for v0.2; stage Dual Sphere as v0.2.x template.
- Parameter discovery order when multiple components expose similarly named fields (tie-breakers).
- Optional `--persist` flag: POST validated assets to MCP → backend → SSOT examples directory.

## Appendix: Minimal Shader (reference only)
```glsl
uniform vec2 u_resolution;
uniform float u_time;
uniform float u_px;
uniform float u_py;
uniform float u_r;

float circleSDF(vec2 p, float r) {
  return length(p) - r;
}

void main() {
  vec2 st = (gl_FragCoord.xy / u_resolution.xy) * 2.0 - 1.0;
  st.x *= u_resolution.x / u_resolution.y;
  vec2 p = st - vec2(u_px, u_py);
  float d = circleSDF(p, u_r);
  float c = 1.0 - smoothstep(-0.01, 0.01, d);
  gl_FragColor = vec4(vec3(c), 1.0);
}
```
