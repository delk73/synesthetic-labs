## Summary of repo state
- External Gemini/OpenAI stack enforces env-driven live gating, taxonomy-classified retries, request/response caps, and provenance-rich logging while reusing MCP validation `labs/generator/external.py:L100-L515` `tests/test_external_generator.py:L19-L260` `tests/test_pipeline.py:L200-L240`
- Generator → Critic pipeline persists assets only after MCP review and records strict/mode/transport telemetry for local and external runs `labs/cli.py:L74-L183` `labs/agents/critic.py:L61-L188` `labs/agents/generator.py:L48-L145` `tests/test_pipeline.py:L200-L298`
- Transport resolver keeps TCP as the default, covers STDIO/socket branches, and shares 1 MiB payload caps across validators while docs highlight provenance expectations `labs/mcp_stdio.py:L134-L205` `tests/test_tcp.py:L140-L176` `tests/test_critic.py:L161-L217` `docs/process.md:L41-L45`
- Environment samples and docs describe v0.3.4 live-mode setup, failure taxonomy, and logging layout under `meta/output/labs/` `README.md:L71-L92` `.example.env:L1-L26` `docs/troubleshooting_external.md:L1-L18`

## Top gaps & fixes (3-5 bullets)
- Reject unknown sections or wrong types during normalization instead of silently dropping them; raise structured errors and extend tests to assert the failure `docs/labs_spec.md:L118-L126` `labs/generator/external.py:L609-L633` `tests/test_external_generator.py:L263-L289`
- Perform pre-flight numeric bounds (e.g., haptic intensity ∈ [0,1]) before MCP invocation and document the rejection path `docs/labs_spec.md:L118-L153` `labs/generator/external.py:L538-L608`
- Add the spec-specified `deterministic` CLI engine alias and cover it in pipeline tests and README snippets `docs/labs_spec.md:L57-L62` `labs/cli.py:L82-L96` `tests/test_pipeline.py:L200-L298`

## Alignment with labs_spec.md (table: Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| --- | --- | --- |
| External live calls gate on env keys, inject Authorization headers, and honor retry/backoff taxonomy | Present | `labs/generator/external.py:L118-L515` `tests/test_external_generator.py:L114-L260` |
| `external.jsonl` entries capture provenance, raw_response hash/size, and failure detail | Present | `labs/generator/external.py:L294-L349` `tests/test_external_generator.py:L19-L98` `tests/test_pipeline.py:L229-L240` |
| CLI exposes `--seed/--temperature/--timeout-s/--strict` controls | Present | `labs/cli.py:L82-L135` `tests/test_pipeline.py:L248-L298` |
| Resolver defaults to TCP when unset/invalid and validates transports | Present | `labs/mcp_stdio.py:L134-L205` `tests/test_tcp.py:L140-L176` |
| Socket transport failure surfaces `socket_unavailable` detail | Present | `labs/agents/critic.py:L86-L142` `tests/test_critic.py:L187-L200` |
| `--engine=deterministic` alias available | Missing | `docs/labs_spec.md:L57-L62` `labs/cli.py:L82-L96` |
| Normalization rejects unknown keys and wrong types | Divergent | `docs/labs_spec.md:L118-L126` `labs/generator/external.py:L609-L633` |
| Pre-flight numeric bounds enforced before MCP | Missing | `docs/labs_spec.md:L148-L153` `labs/generator/external.py:L538-L608` |
| Maintainer docs reference transport provenance resolver | Present | `docs/process.md:L41-L45` |

## Generator implementation (table: Component → Status → Evidence)
| Component | Status | Evidence |
| --- | --- | --- |
| AssetAssembler wiring and control pruning | Present | `labs/generator/assembler.py:L44-L118` `tests/test_generator_assembler.py:L12-L37` |
| Seeded determinism and provenance injection | Present | `labs/generator/assembler.py:L50-L102` `tests/test_determinism.py:L8-L27` |
| Generator logs include trace/mode/transport/strict metadata | Present | `labs/agents/generator.py:L48-L87` `tests/test_generator.py:L11-L56` |
| Experiment records capture validation outcome and failure detail | Present | `labs/agents/generator.py:L89-L145` `tests/test_generator.py:L59-L81` |

## Critic implementation (table: Responsibility → Status → Evidence)
| Responsibility | Status | Evidence |
| --- | --- | --- |
| Required field validation and issue reporting | Present | `labs/agents/critic.py:L61-L112` `tests/test_critic.py:L1-L120` |
| Strict vs relaxed MCP handling (validation still invoked) | Present | `labs/agents/critic.py:L101-L173` `tests/test_critic.py:L161-L184` |
| Socket transport failure surfaces `socket_unavailable` detail | Present | `labs/agents/critic.py:L86-L142` `tests/test_critic.py:L187-L200` |
| Rating stubs persist trace/strict/transport metadata | Present | `labs/agents/critic.py:L190-L217` `tests/test_ratings.py:L7-L33` |

## Assembler / Wiring step (bullets: parameter index, dangling reference pruning, provenance)
- Parameter index derived from shader/tone/haptic sections and deterministic IDs when seeded `labs/generator/assembler.py:L50-L102`
- Control mappings pruned to known parameters so dangling references are removed `labs/generator/assembler.py:L64-L90` `tests/test_generator_assembler.py:L12-L37`
- Provenance replicated into asset and meta for traceability `labs/generator/assembler.py:L70-L88` `labs/agents/generator.py:L61-L87`

## Patch lifecycle (bullets: preview, apply, rate stubs, logging)
- Preview logs include trace IDs, strict/mode flags, and transport provenance ahead of patch application `labs/patches.py:L47-L68` `tests/test_patches.py:L11-L32`
- Apply flow routes through CriticAgent, recording MCP review results and failure taxonomy in patches.jsonl `labs/patches.py:L71-L118` `tests/test_patches.py:L33-L66`
- Rate stubs propagate critic rating metadata (trace/strict/transport) for RLHF loops `labs/patches.py:L121-L156` `tests/test_patches.py:L68-L92`

## MCP integration (bullets: STDIO, TCP-default, socket-optional validation; failure handling; strict vs relaxed mode; 1 MiB caps; reason/detail logging; resolver fallback)
- Resolver defaults to TCP on unset/invalid values and is covered by targeted tests `labs/mcp_stdio.py:L134-L205` `tests/test_tcp.py:L140-L176`
- STDIO builder enforces adapter command, normalizes deprecated `SYN_SCHEMAS_DIR`, and emits a single warning `labs/mcp_stdio.py:L150-L168` `tests/test_critic.py:L203-L217`
- Socket transport requires `MCP_SOCKET_PATH` and surfaces `socket_unavailable` detail when misconfigured `labs/mcp_stdio.py:L171-L180` `tests/test_critic.py:L187-L200`
- Shared transport helpers enforce 1 MiB payload caps for TCP/socket validators `labs/transport.py:L1-L86` `labs/mcp_stdio.py:L171-L205` `tests/test_tcp.py:L120-L159` `tests/test_socket.py:L1-L88`
- Critic strict vs relaxed modes always attempt MCP and downgrade outages when `LABS_FAIL_FAST=0` `labs/agents/critic.py:L101-L173` `tests/test_pipeline.py:L248-L298` `tests/test_critic.py:L161-L184`

## External generator integration (bullets: Gemini/OpenAI interface, provenance logging, CLI flags, error handling, MCP-enforced validation)
- Gemini/OpenAI subclasses share env-driven defaults, provider-specific requests, and deterministic mocks `labs/generator/external.py:L677-L760` `tests/test_external_generator.py:L19-L176`
- Attempt history records retries, hashes, and taxonomy-classified failures for review context `labs/generator/external.py:L161-L292` `tests/test_external_generator.py:L64-L229`
- `record_run` / `record_failure` append provenance-rich entries under `meta/output/labs/external.jsonl` `labs/generator/external.py:L294-L349` `tests/test_external_generator.py:L19-L98`
- CLI dispatch uses CriticAgent so external assets must pass MCP before persistence `labs/cli.py:L115-L183` `tests/test_pipeline.py:L200-L244`

## External generation LIVE (v0.3.4) (bullets: env keys, endpoint resolution, Authorization headers, timeout, retry/backoff, size guards, redaction, normalization → schema-valid)
- Live mode toggled via `LABS_EXTERNAL_LIVE` with keys/endpoints drawn from env defaults `.example.env:L1-L26` `labs/generator/external.py:L118-L208`
- `_resolve_live_settings` injects Authorization headers and redacts them for logs `labs/generator/external.py:L447-L470` `tests/test_external_generator.py:L114-L175`
- Exponential backoff with jitter retries only retryable taxonomies `labs/generator/external.py:L161-L258` `tests/test_external_generator.py:L234-L260`
- Request/response bodies enforce 256 KiB / 1 MiB caps before transport or parsing `labs/generator/external.py:L165-L205` `labs/generator/external.py:L474-L515` `tests/test_external_generator.py:L177-L216`
- Normalization fills required sections, controls, and provenance for schema-valid assets `labs/generator/external.py:L538-L608` `tests/test_external_generator.py:L19-L61`

## Test coverage (table: Feature → Tested? → Evidence, including socket failure coverage, resolver fallback, header injection, size caps, retry taxonomy)
| Feature | Tested? | Evidence |
| --- | --- | --- |
| Generator → Critic pipeline persists validated assets | Yes | `tests/test_pipeline.py:L200-L244` |
| CLI flags precedence (`--seed/--temperature/--timeout-s/--relaxed`) | Yes | `tests/test_pipeline.py:L248-L298` |
| External header injection and redaction in live mode | Yes | `tests/test_external_generator.py:L114-L175` |
| External request/response size caps (256 KiB / 1 MiB) | Yes | `tests/test_external_generator.py:L177-L216` |
| Retry taxonomy (auth no retry, rate limited retries) | Yes | `tests/test_external_generator.py:L218-L260` |
| Normalization defaults fill required sections | Yes | `tests/test_external_generator.py:L263-L289` |
| Resolver fallback to TCP default | Yes | `tests/test_tcp.py:L140-L176` |
| Critic socket failure surfaces `socket_unavailable` detail | Yes | `tests/test_critic.py:L187-L200` |
| Normalization rejects unknown keys | No | `docs/labs_spec.md:L118-L126` `labs/generator/external.py:L609-L633` |
| Pre-flight numeric bounds before MCP | No | `docs/labs_spec.md:L148-L153` `labs/generator/external.py:L538-L608` |

## Dependencies and runtime (table: Package → Used in → Required/Optional)
| Package | Used in | Required/Optional |
| --- | --- | --- |
| `pytest` | Test suite execution | Optional (`requirements.txt:L1`) |

## Environment variables (bullets: name, default, transport defaults, behavior when MCP/external API unreachable, deprecated knobs)
- `MCP_ENDPOINT` selects `tcp|stdio|socket` with TCP fallback on unset/invalid values `docs/labs_spec.md:L64-L83` `labs/mcp_stdio.py:L134-L205`
- `MCP_HOST` / `MCP_PORT` are required for TCP transport `docs/labs_spec.md:L68-L71` `labs/mcp_stdio.py:L182-L199`
- `MCP_ADAPTER_CMD` and deprecated `SYN_SCHEMAS_DIR` configure STDIO adapters with a single-warning deprecation `docs/labs_spec.md:L71-L83` `labs/mcp_stdio.py:L150-L168`
- `MCP_SOCKET_PATH` required when using socket transport; absence yields `socket_unavailable` `docs/labs_spec.md:L72-L73` `labs/mcp_stdio.py:L171-L180` `tests/test_critic.py:L187-L200`
- `LABS_FAIL_FAST` toggles strict/relaxed behavior and defaults to strict when unset `docs/labs_spec.md:L73-L74` `labs/agents/critic.py:L18-L29` `labs/cli.py:L120-L123`
- `LABS_EXPERIMENTS_DIR` controls persistence location for validated assets `.example.env:L1-L26` `labs/cli.py:L28-L43`
- `LABS_EXTERNAL_LIVE`, `GEMINI_*`, `OPENAI_*`, `OPENAI_TEMPERATURE` drive external engines and defaults `.example.env:L1-L26` `labs/generator/external.py:L118-L208`
- `LABS_SOCKET_TESTS` gates Unix socket tests in constrained environments `docs/labs_spec.md:L82-L83` `tests/test_socket.py:L1-L15`

## Logging (bullets: structured JSONL, provenance fields, patch/rating/external fields, reason/detail on transport failures, location under meta/output/)
- `log_jsonl` ensures append-only JSONL with directory creation and timestamps `labs/logging.py:L10-L35`
- Generator, critic, and patch logs capture trace IDs, strict/mode flags, transport, and validation outcomes `labs/agents/generator.py:L48-L145` `labs/agents/critic.py:L61-L188` `labs/patches.py:L47-L156` `tests/test_generator.py:L11-L81` `tests/test_patches.py:L11-L92`
- External generator logs include request parameters, redacted headers, raw_response hash/size, provenance, and failure reason/detail `labs/generator/external.py:L294-L349` `tests/test_external_generator.py:L19-L98` `tests/test_pipeline.py:L229-L240`

## Documentation accuracy (bullets: README vs. labs_spec.md; TCP as default, socket optional; maintainer docs reference resolver; env cleanup; v0.3.4 setup for API keys/live mode)
- README covers TCP defaults, optional transports, CLI engine usage, and live-mode setup matching the spec `README.md:L71-L92` `docs/labs_spec.md:L57-L112`
- `.example.env` enumerates MCP and external engine variables with defaults and deprecation notes `.example.env:L1-L26` `docs/labs_spec.md:L64-L84`
- Maintainer process doc explicitly references `resolve_mcp_endpoint` to avoid drift `docs/process.md:L41-L45`
- Troubleshooting guide maps failure taxonomy and redaction practices `docs/troubleshooting_external.md:L1-L18`
- README/CLI docs omit the `deterministic` alias that appears in the spec `docs/labs_spec.md:L57-L62` `README.md:L71-L84`

## Detected divergences
- Normalization drops unknown keys instead of rejecting them per spec `labs/generator/external.py:L609-L633` `docs/labs_spec.md:L118-L126`
- Pre-flight numeric bounds (e.g., haptic intensity range) are not enforced before MCP validation `labs/generator/external.py:L538-L608` `docs/labs_spec.md:L148-L153`
- CLI omits the spec-defined `--engine=deterministic` alias `labs/cli.py:L82-L96` `docs/labs_spec.md:L57-L62`

## Recommendations
- Implement explicit rejection for unknown or incorrectly typed sections during normalization and add regression tests covering the failure paths `labs/generator/external.py:L538-L633` `tests/test_external_generator.py:L263-L289`
- Add pre-flight validators for numeric bounds (intensity, parameter ranges) before calling MCP, with unit coverage for the rejection taxonomy `labs/generator/external.py:L538-L608` `docs/labs_spec.md:L148-L153`
- Extend the CLI and documentation to support `--engine=deterministic`, and cover the alias in pipeline tests `labs/cli.py:L82-L183` `tests/test_pipeline.py:L200-L298` `docs/labs_spec.md:L57-L62`
