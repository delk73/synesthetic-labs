## Summary of repo state
- Generator and CLI remain pre-schema-awareness: assets always use the local `$schema` path and there is no schema_version input, so branching required for 0.7.3 vs 0.7.4 never occurs.【F:docs/labs_spec.md†L28-L96】【F:labs/generator/assembler.py†L23-L110】【F:labs/cli.py†L82-L135】
- Critic, MCP resolver, and patch lifecycle continue to enforce transport defaults, strict vs relaxed handling, and shared logging per the earlier v0.3.4 scope.【F:labs/agents/critic.py†L35-L218】【F:labs/mcp_stdio.py†L162-L232】【F:labs/patches.py†L1-L159】
- External generator integrations (Gemini/OpenAI) still cover env-gated live calls, retries, normalization, and logging, but logs omit schema_version metadata required by the updated spec.【F:labs/generator/external.py†L166-L339】【F:tests/test_external_generator.py†L117-L260】

## Top gaps & fixes (3-5 bullets)
- Add schema_version plumbing (env + CLI flag) and generator branching to satisfy the v0.3.4 schema-targeting objectives.【F:docs/labs_spec.md†L28-L96】【F:labs/cli.py†L82-L135】【F:labs/generator/assembler.py†L23-L110】
- Switch `$schema` tagging to the versioned corpus URL derived from schema_version instead of the bundled relative path.【F:docs/labs_spec.md†L78-L133】【F:labs/generator/assembler.py†L23-L110】
- Extend external generation context/logging to include schema_version and a null failure field on success per the logging contract.【F:docs/labs_spec.md†L113-L133】【F:labs/generator/external.py†L230-L339】

## Alignment with labs_spec.md (table: Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| --- | --- | --- |
| Spec version pinned to v0.3.4 | Divergent | Document already states v0.3.5 scope, so repo spec drifted ahead of requested audit version.【F:docs/labs_spec.md†L1-L33】 |
| Generator exposes schema_version argument + env precedence | Missing | No CLI flag/env handling; generator API still seed-only.【F:docs/labs_spec.md†L39-L64】【F:labs/cli.py†L82-L135】 |
| Generator branches 0.7.3 vs ≥0.7.4 fields | Missing | AssetAssembler always emits enriched fields regardless of schema version controls that do not exist.【F:docs/labs_spec.md†L30-L96】【F:labs/generator/assembler.py†L66-L110】 |
| `$schema` URL points at chosen corpus | Divergent | Output keeps static `meta/schemas/...` path instead of versioned HTTPS URL.【F:docs/labs_spec.md†L78-L133】【F:labs/generator/assembler.py†L23-L102】 |
| External logs capture schema_version + `$schema` | Missing | record_run omits schema_version and `$schema` snapshot in external.jsonl entries.【F:docs/labs_spec.md†L113-L133】【F:labs/generator/external.py†L230-L339】 |
| MCP validation strict/relaxed parity | Present | Critic enforces fail-fast defaults, downgrades in relaxed mode, and surfaces transport errors.【F:labs/agents/critic.py†L61-L188】【F:tests/test_critic.py†L15-L204】 |
| External normalization + bounds checks | Present | Normalizer rejects unknown keys, enforces numeric ranges, and tests cover failures.【F:labs/generator/external.py†L639-L780】【F:tests/test_external_generator.py†L266-L365】 |
| Retry/backoff + size caps | Present | Generator enforces 256KiB/1MiB guards and exponential retries with coverage.【F:labs/generator/external.py†L166-L214】【F:tests/test_external_generator.py†L180-L260】 |
| TCP default resolver fallback | Present | Resolver returns TCP when unset/invalid with unit tests locking behavior.【F:labs/mcp_stdio.py†L162-L210】【F:tests/test_tcp.py†L175-L188】 |

## Generator implementation (table: Component → Status → Evidence)
| Component | Status | Evidence |
| --- | --- | --- |
| AssetAssembler deterministic IDs/timestamps | Present | Seeded runs derive stable UUID/timestamp pairs.【F:labs/generator/assembler.py†L112-L120】 |
| Parameter index aggregation + control pruning | Present | Parameter index built from sections; controls pruned to known parameters.【F:labs/generator/assembler.py†L122-L141】 |
| Provenance scaffolding | Present | GeneratorAgent backfills provenance/trace metadata and logs experiments.【F:labs/agents/generator.py†L30-L145】【F:tests/test_generator.py†L11-L87】 |
| Schema-version branching | Missing | No schema_version input or conditional fields implemented.【F:docs/labs_spec.md†L28-L96】【F:labs/generator/assembler.py†L66-L110】 |

## Critic implementation (table: Responsibility → Status → Evidence)
| Responsibility | Status | Evidence |
| --- | --- | --- |
| Required-field checks + trace resolution | Present | Critic enforces core keys and derives trace_id from asset provenance.【F:labs/agents/critic.py†L35-L185】 |
| MCP bridge + resolver fallback | Present | Critic builds validators from env and reports transport-specific errors.【F:labs/agents/critic.py†L96-L188】【F:tests/test_critic.py†L15-L204】 |
| Strict vs relaxed behavior | Present | Fail-fast default toggled by LABS_FAIL_FAST with warning downgrade tests.【F:labs/agents/critic.py†L61-L173】【F:tests/test_critic.py†L162-L204】 |
| Rating log stubs | Present | record_rating persists structured entries with transport metadata.【F:labs/agents/critic.py†L190-L218】【F:tests/test_patches.py†L65-L92】 |

## Assembler / Wiring step (bullets: parameter index, dangling reference pruning, provenance)
- `parameter_index` gathers shader/tone/haptic inputs for downstream validation.【F:labs/generator/assembler.py†L122-L130】
- Control mappings that lack a known parameter are dropped before output.【F:labs/generator/assembler.py†L131-L141】
- Asset/meta provenance embeds generator IDs, version, and trace timestamps for reproducibility.【F:labs/generator/assembler.py†L80-L110】

## Patch lifecycle (bullets: preview, apply, rate stubs, logging)
- `preview_patch` logs action, changes, and transport metadata to JSONL.【F:labs/patches.py†L47-L69】【F:tests/test_patches.py†L11-L29】
- `apply_patch` merges updates, revalidates via Critic, and records failures with reasons.【F:labs/patches.py†L71-L118】【F:tests/test_patches.py†L31-L63】
- `rate_patch` appends RLHF stubs linked to critic rating entries under the same log stream.【F:labs/patches.py†L121-L156】【F:tests/test_patches.py†L65-L92】

## MCP integration (bullets: STDIO, TCP-default, socket-optional validation; failure handling; strict vs relaxed mode; 1 MiB caps; reason/detail logging; resolver fallback)
- Resolver defaults to TCP when unset/invalid and supports stdio/socket overrides documented in builder.【F:labs/mcp_stdio.py†L162-L232】
- STDIO builder forwards deprecated SYN_SCHEMAS_DIR once with warning while socket path validation raises socket_unavailable.【F:labs/mcp_stdio.py†L178-L207】【F:tests/test_critic.py†L188-L217】
- TCP client enforces payload caps via shared transport helpers that raise classified errors.【F:labs/transport.py†L1-L91】【F:tests/test_tcp.py†L160-L172】
- Critic surfaces `mcp_unavailable` vs `mcp_error` reasons and toggles strict vs relaxed behavior through LABS_FAIL_FAST.【F:labs/agents/critic.py†L61-L188】【F:tests/test_critic.py†L55-L204】

## External generator integration (bullets: Gemini/OpenAI interface, provenance logging, CLI flags, error handling, MCP-enforced validation)
- Gemini/OpenAI subclasses inherit shared request envelope, live/mock dispatch, and provenance assembly hooks.【F:labs/generator/external.py†L300-L1040】
- CLI delegates to external generators, records only MCP-reviewed assets, and logs review metadata.【F:labs/cli.py†L115-L178】【F:tests/test_pipeline.py†L229-L274】
- External runs log attempts with hashed response metadata and validation outcomes, differentiating success vs failure contexts.【F:labs/generator/external.py†L166-L355】【F:tests/test_external_generator.py†L43-L145】

## External generation LIVE (v0.3.4) (bullets: env keys, endpoint resolution, Authorization headers, timeout, retry/backoff, size guards, redaction, normalization → schema-valid)
- Live mode gated by `LABS_EXTERNAL_LIVE` plus provider API keys/endpoints with sanitized header logging.【F:labs/generator/external.py†L82-L207】【F:tests/test_external_generator.py†L117-L178】
- Authorization headers injected for live calls, redacted in logs, and endpoints resolved from env/defaults.【F:labs/generator/external.py†L438-L467】【F:tests/test_external_generator.py†L117-L145】
- Retries implement exponential backoff with jitter and respect no-retry taxonomy; size caps enforce 256 KiB/1 MiB limits prior to parsing.【F:labs/generator/external.py†L166-L214】【F:tests/test_external_generator.py†L180-L260】
- Normalization fills defaults, rejects unknown keys, and enforces numeric bounds before MCP review.【F:labs/generator/external.py†L639-L780】【F:tests/test_external_generator.py†L266-L365】

## Test coverage (table: Feature → Tested? → Evidence, including socket failure coverage, resolver fallback, header injection, size caps, retry taxonomy)
| Feature | Tested? | Evidence |
| --- | --- | --- |
| Critic socket failure detail | Yes | Relaxed/socket tests expect `socket_unavailable` detail.【F:tests/test_critic.py†L188-L204】 |
| Resolver TCP fallback | Yes | Explicit tests assert TCP default on unset/invalid env.【F:tests/test_tcp.py†L175-L188】 |
| Header injection & redaction | Yes | Live header test checks Authorization injection/redaction.【F:tests/test_external_generator.py†L117-L176】 |
| Request/response size caps | Yes | Oversized body tests raise bad_response taxonomy.【F:tests/test_external_generator.py†L180-L219】 |
| Retry/backoff taxonomy | Yes | Rate-limit test retries until success under expected reasons.【F:tests/test_external_generator.py†L221-L260】 |
| Schema-version branching/unit matrix | No | Spec demands 0.7.3/0.7.4 tests, but generator tests only cover legacy fields/logging.【F:docs/labs_spec.md†L136-L146】【F:tests/test_generator.py†L11-L87】 |

## Dependencies and runtime (table: Package → Used in → Required/Optional)
| Package | Used in | Required/Optional |
| --- | --- | --- |
| jsonschema | MCP validation helpers load schema files for asset checks.【F:mcp/validate.py†L9-L96】 | Required |
| pytest | Test suite imports pytest fixtures across unit tests.【F:tests/test_critic.py†L1-L217】 | Optional (dev/test) |

## Environment variables (bullets: name, default, transport defaults, behavior when MCP/external API unreachable, deprecated knobs)
- `MCP_ENDPOINT` controls stdio/socket/tcp transports with TCP fallback when unset or invalid.【F:labs/mcp_stdio.py†L162-L210】
- `MCP_HOST`/`MCP_PORT` feed TCP validator; missing values raise MCPUnavailableError for strict handling.【F:labs/mcp_stdio.py†L210-L229】
- `MCP_ADAPTER_CMD` and deprecated `SYN_SCHEMAS_DIR` apply only to STDIO with single warning emission.【F:labs/mcp_stdio.py†L178-L196】【F:tests/test_critic.py†L204-L217】
- `LABS_FAIL_FAST` toggles strict vs relaxed behavior across critic, generator, and patches.【F:labs/agents/critic.py†L61-L173】【F:labs/patches.py†L17-L66】
- `LABS_EXTERNAL_LIVE`, provider keys (`GEMINI_API_KEY`, `OPENAI_API_KEY`), and endpoints gate live external traffic; defaults keep mock mode enabled.【F:labs/generator/external.py†L82-L207】【F:.example.env†L18-L26】
- `LABS_SCHEMA_VERSION` env from spec is absent, leaving schema targeting unconfigurable.【F:docs/labs_spec.md†L67-L72】【F:.example.env†L1-L26】

## Logging (bullets: structured JSONL, provenance fields, patch/rating/external fields, reason/detail on transport failures, location under meta/output/)
- `log_jsonl` appends structured entries under `meta/output/labs/` with auto directory creation.【F:labs/logging.py†L10-L35】
- GeneratorAgent, CriticAgent, and patches append trace/mode/transport-rich records for proposals, reviews, and lifecycle steps.【F:labs/agents/generator.py†L30-L145】【F:labs/agents/critic.py†L164-L218】【F:labs/patches.py†L47-L156】
- External generator logs capture attempts, raw response hashes, and validation results, but omit schema_version and null failure on success.【F:labs/generator/external.py†L230-L355】
- external.jsonl/critic/generator logs reside beneath `meta/output/labs/`, matching documented structure.【F:labs/logging.py†L10-L35】【F:tests/test_external_generator.py†L43-L145】

## Documentation accuracy (bullets: README vs. labs_spec.md; TCP as default, socket optional; maintainer docs reference resolver; env cleanup; v0.3.4 setup for API keys/live mode)
- README still describes `$schema` enforcement and TCP default transports but lacks schema_version guidance now mandated by spec.【F:README.md†L41-L76】
- Maintainer process doc reiterates resolver responsibilities to avoid transport drift.【F:docs/process.md†L41-L45】
- README and `.example.env` detail TCP default, optional socket, and live external env setup consistent with v0.3.4 behavior.【F:README.md†L19-L104】【F:.example.env†L1-L26】
- Spec file itself advertises v0.3.5 objectives, signaling documentation drift from requested v0.3.4 audit baseline.【F:docs/labs_spec.md†L1-L96】

## Detected divergences
- Spec document already targets v0.3.5 schema-awareness despite audit scope stating v0.3.4.【F:docs/labs_spec.md†L1-L96】
- Generator lacks schema_version branching and keeps static `$schema` paths, failing updated normalization rules.【F:docs/labs_spec.md†L28-L96】【F:labs/generator/assembler.py†L23-L110】
- External logs omit schema_version metadata and null failure entries on success contrary to the logging contract.【F:docs/labs_spec.md†L113-L133】【F:labs/generator/external.py†L230-L339】

## Recommendations
- Implement schema_version inputs (env + CLI) and branch AssetAssembler output to honor 0.7.3 legacy vs 0.7.4+ enriched payloads.【F:docs/labs_spec.md†L28-L96】【F:labs/cli.py†L82-L135】【F:labs/generator/assembler.py†L66-L110】
- Derive `$schema` URLs from the selected schema_version to reference hosted corpus files rather than local relative paths.【F:docs/labs_spec.md†L78-L133】【F:labs/generator/assembler.py†L23-L102】
- Extend external generator context/log writers to include schema_version, `$schema`, and `failure: null` on success, updating tests accordingly.【F:docs/labs_spec.md†L113-L133】【F:labs/generator/external.py†L230-L339】【F:tests/test_external_generator.py†L43-L176】
