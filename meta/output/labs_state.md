## Summary of repo state
- Schema targeting now flows through CLI flag, env fallback, and assembler branching, though the default constant remains 0.7.4 instead of the spec’s 0.7.3 baseline.【F:labs/cli.py†L52-L146】【F:labs/generator/assembler.py†L23-L210】【F:docs/labs_spec.md†L33-L76】
- Critic, MCP resolver, and patch lifecycle continue to enforce strict vs relaxed validation with transport-aware logging backed by unit tests.【F:labs/agents/critic.py†L61-L218】【F:labs/mcp_stdio.py†L162-L232】【F:labs/patches.py†L47-L156】【F:tests/test_critic.py†L15-L204】
- External generators meet live-mode requirements: env-gated keys, header redaction, retry/backoff, numeric bounds, and logging now include schema_version metadata.【F:labs/generator/external.py†L82-L840】【F:tests/test_external_generator.py†L43-L260】【F:tests/test_pipeline.py†L244-L306】
- Documentation lags the implementation: spec header already says v0.3.5, and README/.example.env omit schema-version guidance required by the spec.【F:docs/labs_spec.md†L1-L72】【F:README.md†L19-L104】【F:.example.env†L1-L26】

## Top gaps & fixes (3-5 bullets)
- Align `AssetAssembler.DEFAULT_SCHEMA_VERSION` (and related tests/docs) with the spec’s 0.7.3 default or revise the spec header to match the new baseline.【F:labs/generator/assembler.py†L16-L36】【F:docs/labs_spec.md†L61-L76】
- Extend README and `.example.env` to document the new `--schema-version` flag and `LABS_SCHEMA_VERSION` precedence so operators can target legacy schemas intentionally.【F:labs/cli.py†L52-L138】【F:README.md†L41-L76】【F:.example.env†L1-L26】
- Clarify the spec header/scope to indicate whether v0.3.4 or v0.3.5 is authoritative for this audit cycle.【F:docs/labs_spec.md†L1-L40】

## Alignment with labs_spec.md (table: Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| --- | --- | --- |
| Spec version header matches v0.3.4 scope | Divergent | Spec front matter already declares v0.3.5 objectives while the audit prompt targets v0.3.4.【F:docs/labs_spec.md†L1-L48】 |
| CLI flag + env precedence (`--schema-version` > `LABS_SCHEMA_VERSION` > default) | Present | CLI adds the flag with env fallback and pipeline tests assert precedence.【F:labs/cli.py†L58-L140】【F:tests/test_pipeline.py†L228-L317】 |
| Generator branches 0.7.3 legacy vs ≥0.7.4 enriched assets | Present | AssetAssembler routes through `_build_legacy_asset`/`_build_enriched_asset` and tests validate both shapes.【F:labs/generator/assembler.py†L68-L210】【F:tests/test_generator_assembler.py†L1-L87】 |
| `$schema` URL derived from schema_version template | Present | SCHEMA_URL_TEMPLATE resolves to hosted corpus URLs and CLI/CLI tests assert `$schema` propagation.【F:labs/generator/assembler.py†L16-L54】【F:tests/test_pipeline.py†L244-L306】 |
| Default schema version remains 0.7.3 | Divergent | Code defaults to 0.7.4 while the spec keeps 0.7.3 as baseline.【F:labs/generator/assembler.py†L16-L24】【F:docs/labs_spec.md†L61-L76】 |
| External logs capture schema_version, `$schema`, and failure payload | Present | `record_run` writes these fields and tests assert `schema_version` plus `failure` null when validation passes.【F:labs/generator/external.py†L230-L320】【F:tests/test_pipeline.py†L244-L306】【F:tests/test_external_generator.py†L43-L120】 |
| Critic strict vs relaxed always invokes MCP | Present | Critic toggles fail-fast, surfaces `mcp_unavailable` reasons, and tests cover relaxed mode downgrades.【F:labs/agents/critic.py†L61-L188】【F:tests/test_critic.py†L55-L204】 |
| Normalization rejects unknown keys & out-of-range values | Present | `_normalise_asset` enforces allowed keys and `_validate_bounds` checks numeric ranges with failing tests.【F:labs/generator/external.py†L639-L840】【F:tests/test_external_generator.py†L266-L365】 |
| Retry/backoff & size caps follow taxonomy | Present | External generator enforces 256 KiB/1 MiB caps and exponential retries; tests assert taxonomy adherence.【F:labs/generator/external.py†L166-L214】【F:tests/test_external_generator.py†L180-L260】 |
| TCP fallback when endpoint unset/invalid | Present | Resolver defaults to TCP and tests lock both unset and bogus values.【F:labs/mcp_stdio.py†L162-L210】【F:tests/test_tcp.py†L175-L188】 |
| Maintainer docs reference schema-version targeting controls | Missing | README and `.example.env` document transports but omit schema-version flag/env guidance.【F:README.md†L19-L104】【F:.example.env†L1-L26】【F:docs/process.md†L39-L60】 |

## Generator implementation (table: Component → Status → Evidence)
| Component | Status | Evidence |
| --- | --- | --- |
| CLI `--schema-version` flag & env fallback | Present | Flag surfaces in CLI parser with precedence tests covering seed/temperature overrides and schema routing.【F:labs/cli.py†L52-L146】【F:tests/test_pipeline.py†L228-L317】 |
| AssetAssembler schema branching & hosted `$schema` URLs | Present | `_is_legacy_schema` selects legacy builder, enriched assets include provenance/parameter_index, and tests assert both forms.【F:labs/generator/assembler.py†L68-L210】【F:tests/test_generator_assembler.py†L1-L87】 |
| GeneratorAgent logging & experiment recording | Present | Agent logs schema_version, trace, and validation metadata; unit tests confirm persistence entries.【F:labs/agents/generator.py†L34-L195】【F:tests/test_generator.py†L11-L118】 |
| Default schema constant matches spec baseline | Divergent | `DEFAULT_SCHEMA_VERSION` is `0.7.4`, conflicting with spec’s required default of `0.7.3`.【F:labs/generator/assembler.py†L16-L24】【F:docs/labs_spec.md†L61-L76】 |

## Critic implementation (table: Responsibility → Status → Evidence)
| Responsibility | Status | Evidence |
| --- | --- | --- |
| Required-field checks & trace resolution | Present | Critic inspects enriched assets, derives `trace_id`, and logs issues when keys missing.【F:labs/agents/critic.py†L74-L150】 |
| MCP bridge & resolver fallback | Present | Critic builds validators via `build_validator_from_env`, handling stdio/socket/tcp failures with taxonomy detail.【F:labs/agents/critic.py†L96-L188】【F:tests/test_critic.py†L15-L204】 |
| Strict vs relaxed behavior | Present | LABS_FAIL_FAST toggles failure vs warning paths and tests assert downgraded reviews.【F:labs/agents/critic.py†L61-L173】【F:tests/test_critic.py†L154-L204】 |
| Rating log stubs | Present | `record_rating` emits structured JSONL entries mirrored in patch lifecycle tests.【F:labs/agents/critic.py†L190-L218】【F:tests/test_patches.py†L65-L92】 |

## Assembler / Wiring step (bullets: parameter index, dangling reference pruning, provenance)
- `parameter_index` aggregates shader/tone/haptic inputs and deduplicates before enrichment.【F:labs/generator/assembler.py†L122-L170】
- `_prune_controls` drops mappings whose parameters are absent from the index, avoiding dangling references.【F:labs/generator/assembler.py†L131-L141】
- Provenance blocks capture timestamps, seeds, asset IDs, and generator metadata for deterministic replay.【F:labs/generator/assembler.py†L80-L118】【F:labs/agents/generator.py†L94-L166】

## Patch lifecycle (bullets: preview, apply, rate stubs, logging)
- `preview_patch` writes structured audit events including trace, strict flag, and transport metadata.【F:labs/patches.py†L47-L74】【F:tests/test_patches.py†L11-L29】
- `apply_patch` invokes Critic, records validation outcome, and surfaces failure reason/detail when review fails.【F:labs/patches.py†L76-L118】【F:tests/test_patches.py†L31-L63】
- `rate_patch` records RLHF stubs and links to critic rating logs with shared trace IDs.【F:labs/patches.py†L121-L156】【F:tests/test_patches.py†L65-L92】

## MCP integration (bullets: STDIO, TCP-default, socket-optional validation; failure handling; strict vs relaxed mode; 1 MiB caps; reason/detail logging; resolver fallback)
- `resolve_mcp_endpoint` defaults to TCP, validates stdio/socket envs, and emits deprecated SYN_SCHEMAS_DIR warning once.【F:labs/mcp_stdio.py†L162-L232】【F:tests/test_critic.py†L188-L217】
- Shared transport helpers cap payloads at 1 MiB and surface errors via MCPUnavailableError during TCP validation.【F:labs/transport.py†L1-L96】【F:tests/test_tcp.py†L110-L172】
- Critic logs `mcp_unavailable`/`mcp_error` reasons under strict mode and downgrades to warnings when LABS_FAIL_FAST is disabled.【F:labs/agents/critic.py†L96-L188】【F:tests/test_critic.py†L55-L204】

## External generator integration (bullets: Gemini/OpenAI interface, provenance logging, CLI flags, error handling, MCP-enforced validation)
- Gemini/OpenAI implementations reuse shared request envelope, live/mock dispatch, and normalization pipeline that injects provenance metadata.【F:labs/generator/external.py†L300-L880】
- CLI generate command wires schema_version through external generators and only records runs after Critic review.【F:labs/cli.py†L115-L211】【F:tests/test_pipeline.py†L228-L317】
- `record_run`/`record_failure` append attempts, raw response hashes, schema_version, and validation outcomes to `meta/output/labs/external.jsonl`.【F:labs/generator/external.py†L230-L355】【F:tests/test_external_generator.py†L43-L145】

## External generation LIVE (v0.3.4) (bullets: env keys, endpoint resolution, Authorization headers, timeout, retry/backoff, size guards, redaction, normalization → schema-valid)
- Live mode requires `LABS_EXTERNAL_LIVE=1` plus provider API keys; Authorization headers are redacted in logs.【F:labs/generator/external.py†L82-L215】【F:tests/test_external_generator.py†L117-L176】
- Request and response payloads respect 256 KiB / 1 MiB caps before parsing, raising taxonomy-aligned errors when exceeded.【F:labs/generator/external.py†L166-L214】【F:tests/test_external_generator.py†L180-L219】
- Exponential backoff with jitter retries retryable errors and stops on non-retry reasons such as `auth_error`.【F:labs/generator/external.py†L166-L214】【F:tests/test_external_generator.py†L221-L260】
- Normalization enforces allowed keys, numeric bounds, and fills provenance before delegating to MCP validation.【F:labs/generator/external.py†L639-L840】【F:tests/test_external_generator.py†L266-L365】
- external.jsonl entries record schema_version, `$schema`, and experiment linkage after successful runs.【F:labs/generator/external.py†L230-L320】【F:tests/test_pipeline.py†L244-L306】

## Test coverage (table: Feature → Tested? → Evidence, including socket failure coverage, resolver fallback, header injection, size caps, retry taxonomy)
| Feature | Tested? | Evidence |
| --- | --- | --- |
| Schema-version branching/unit matrix | Yes | Unit tests assert 0.7.3 legacy assets vs 0.7.4 enriched structure and generator logs.【F:tests/test_generator_assembler.py†L1-L87】【F:tests/test_generator.py†L44-L87】 |
| CLI flag precedence & relaxed mode plumbing | Yes | Pipeline tests verify schema_version routing, seed/temperature overrides, and LABS_FAIL_FAST toggling.【F:tests/test_pipeline.py†L228-L317】 |
| Critic socket failure detail | Yes | Socket path test asserts `socket_unavailable` detail in review payload.【F:tests/test_critic.py†L188-L204】 |
| Resolver TCP fallback | Yes | Tests cover unset and invalid MCP_ENDPOINT values returning TCP.【F:tests/test_tcp.py†L175-L188】 |
| Header injection & redaction | Yes | Live header test checks Authorization injection and log redaction.【F:tests/test_external_generator.py†L117-L176】 |
| Size caps & retry taxonomy | Yes | Oversized body and rate-limit tests exercise bad_response and rate_limited branches.【F:tests/test_external_generator.py†L180-L260】 |
| Normalization rejects unknown/out-of-range | Yes | Tests raise `bad_response` for unknown keys and out-of-range parameter defaults.【F:tests/test_external_generator.py†L266-L365】 |

## Dependencies and runtime (table: Package → Used in → Required/Optional)
| Package | Used in | Required/Optional |
| --- | --- | --- |
| jsonschema | MCP validation helpers load schemas and generator schema tests validate assets.【F:labs/mcp/validate.py†L1-L96】【F:tests/test_generator_schema.py†L1-L40】 | Required |
| pytest | Entire test suite leverages pytest fixtures/marks for coverage.【F:requirements.txt†L1-L2】【F:tests/test_critic.py†L1-L12】 | Optional (dev/test) |

## Environment variables (bullets: name, default, transport defaults, behavior when MCP/external API unreachable, deprecated knobs)
- `LABS_SCHEMA_VERSION` overrides generator/CLI defaults; absent values fall back to 0.7.4, creating the noted divergence with the spec baseline.【F:labs/cli.py†L58-L86】【F:labs/agents/generator.py†L42-L86】
- `LABS_FAIL_FAST` controls strict vs relaxed behavior across generator, critic, and patch modules.【F:labs/agents/critic.py†L61-L86】【F:labs/agents/generator.py†L19-L34】【F:labs/patches.py†L13-L38】
- `LABS_EXPERIMENTS_DIR` defines persistence location for generated assets written via CLI.【F:labs/cli.py†L18-L64】
- `LABS_EXTERNAL_LIVE`, `GEMINI_API_KEY`, `OPENAI_API_KEY`, and related endpoint/model vars gate live external calls with redacted logging defaults.【F:labs/generator/external.py†L82-L191】【F:.example.env†L14-L33】
- `MCP_ENDPOINT`, `MCP_HOST`, `MCP_PORT`, `MCP_ADAPTER_CMD`, `MCP_SOCKET_PATH`, and deprecated `SYN_SCHEMAS_DIR` govern validator transports and surface explicit error messages when misconfigured.【F:labs/mcp_stdio.py†L162-L232】【F:.example.env†L1-L18】【F:tests/test_critic.py†L188-L217】

## Logging (bullets: structured JSONL, provenance fields, patch/rating/external fields, reason/detail on transport failures, location under meta/output/)
- `log_jsonl` guarantees append-only JSONL with timestamp injection, ensuring logs under `meta/output/labs/` stay structured.【F:labs/logging.py†L10-L35】
- Generator, critic, and patch modules log schema_version, transport, strict mode, and trace identifiers for reproducibility.【F:labs/agents/generator.py†L118-L195】【F:labs/agents/critic.py†L170-L218】【F:labs/patches.py†L47-L156】
- External generator logs include attempts, response hashes, schema_version, `$schema`, and failure payloads per spec.【F:labs/generator/external.py†L230-L320】【F:tests/test_pipeline.py†L244-L306】

## Documentation accuracy (bullets: README vs. labs_spec.md; TCP as default, socket optional; maintainer docs reference resolver; env cleanup; v0.3.4 setup for API keys/live mode)
- README documents MCP transports and external live mode but omits the new schema-version flag/env, leaving operators without guidance on targeting 0.7.3.【F:README.md†L19-L104】
- `.example.env` mirrors transport/env defaults yet lacks `LABS_SCHEMA_VERSION`, reinforcing the documentation gap.【F:.example.env†L1-L26】
- Maintainer process doc references transport resolver best practices but does not mention schema-targeting, partially meeting the spec’s documentation expectations.【F:docs/process.md†L39-L60】
- Spec document header already claims v0.3.5 scope, so spec vs implementation timelines require clarification.【F:docs/labs_spec.md†L1-L48】

## Detected divergences
- Default schema version constant is 0.7.4 while the spec baseline remains 0.7.3, causing precedence drift unless explicitly overridden.【F:labs/generator/assembler.py†L16-L24】【F:docs/labs_spec.md†L61-L76】
- Documentation (README, `.example.env`, process) does not describe schema-version targeting controls mandated by the spec.【F:README.md†L19-L104】【F:.example.env†L1-L26】【F:docs/process.md†L39-L60】
- Spec file versioning (v0.3.5) is ahead of the audit’s v0.3.4 scope, creating expectation ambiguity.【F:docs/labs_spec.md†L1-L48】

## Recommendations
- Decide whether to revert `AssetAssembler.DEFAULT_SCHEMA_VERSION` to 0.7.3 or update the spec/docs to reflect a 0.7.4 baseline, then align tests accordingly.【F:labs/generator/assembler.py†L16-L36】【F:docs/labs_spec.md†L61-L76】
- Update README, `.example.env`, and maintainer docs to document `LABS_SCHEMA_VERSION`, CLI precedence, and schema-targeting workflows for 0.7.3 vs 0.7.4 assets.【F:labs/cli.py†L52-L146】【F:README.md†L19-L104】【F:.example.env†L1-L26】【F:docs/process.md†L39-L60】
- Clarify the spec header/version history so audits reference the correct scope (v0.3.4 vs v0.3.5) and avoid mixed guidance for operators.【F:docs/labs_spec.md†L1-L48】
