# Generator v0.2 — Component + Wiring Design

## Purpose
Evolve Labs Generator from simple proposals to full schema-valid Synesthetic assets. Each section (shader, tone, haptic, etc.) is created by a dedicated component generator. A wiring step enforces consistency across cross-references. Output is always validated against the SSOT schema via MCP.

## Architecture
- **Component Generators**
  - ShaderGenerator: GLSL fragment/vertex, uniforms, input_parameters
  - ToneGenerator: Tone.Synth baseline with input_parameters + optional effects/parts/patterns
  - HapticGenerator: generic device + intensity/frequency input_parameters
  - ControlGenerator: maps user gestures (mouse/keys/wheel) to parameters across sections
  - ModulationGenerator: additive/sine/triangle LFOs targeting valid parameters
  - RuleBundleGenerator: default grid mapping to visual/audio/haptic effects
  - MetaGenerator: description + tags + complexity metadata

- **Assembler / Wiring Step**
  - Collect all input_parameters from shader/tone/haptic
  - Ensure control mappings reference existing parameters
  - Ensure modulations target real parameters (drop/rewrite dangling targets)
  - Ensure rule_bundle effects reference valid parameters
  - Apply provenance (UUID, timestamp, seed) for reproducibility

## Flow
1. Component generators create isolated sections with canonical defaults.
2. Assembler merges them, checks references, and rewrites/omits invalid links.
3. Complete asset validated via MCP against SSOT schema.
4. Persist/log with provenance (UUID, timestamp, prompt, seed).

## Baseline Example
- Shader: CircleSDF with u_px/u_py/u_r
- Tone: Canonical Tone.Synth (volume, detune, envelope, portamento)
- Haptic: Generic intensity + frequency parameters
- Controls: mouse.x → shader.u_px, mouse.y → shader.u_py, Shift+mouse → tone.detune
- Modulations: triangle LFO on shader.u_r, sine on haptic.intensity, triangle on tone.detune
- RuleBundle: Grid press triggers note, haptic pulse, and radius nudge
- Meta: multimodal, medium complexity, tags: [circle, interactive, audio, haptic]

## Testing Strategy
- **Unit Tests**: each component generator yields schema-valid section
- **Integration Tests**: Assembler resolves all references (no dangling targets)
- **E2E Tests**: Generator → Critic → MCP validation → JSONL export (persisted to meta/output/)
- **Determinism Tests**: given a fixed seed, identical asset generated

## Open Questions
- Baseline coverage: start with minimal Circle vs richer Dual Sphere examples?
- Randomization: how much variability vs determinism (seed handling)?
- Provenance: best practice for logging seed/prompt/context in lab exports?
