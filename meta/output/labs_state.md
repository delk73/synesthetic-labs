## Summary of repo state
- External generators now gate live mode on `LABS_EXTERNAL_LIVE`, enforce Authorization headers, redact secrets, normalize assets, and capture failure taxonomy with retry/backoff and size caps `labs/generator/external.py:118-515`; `tests/test_external_generator.py:19-229`
- `labs.cli generate` orchestrates internal and external engines with seed/temperature/timeout/strict flags, persisting MCP-validated assets and logging experiment context `labs/cli.py:82-183`; `tests/test_pipeline.py:200-298`
- Generator, critic, and patch modules emit JSONL logs carrying trace IDs, strict/mode flags, transport provenance, and structured failure detail under `meta/output/labs/` `labs/agents/generator.py:61-145`; `labs/agents/critic.py:164-188`; `labs/patches.py:55-156`; `tests/test_patches.py:11-88`
- MCP validation resolves transports with TCP as the default, exercises STDIO/socket branches, and enforces 1 MiB caps through shared helpers `labs/mcp_stdio.py:134-199`; `tests/test_tcp.py:140-176`; `tests/test_socket.py:1-88`; `tests/test_critic.py:187-200`
- Docs and env samples describe live-call setup, troubleshooting taxonomy, and resolver expectations `README.md:71-92`; `.example.env:1-26`; `docs/troubleshooting_external.md:1-18`; `docs/process.md:31-46`

## Top gaps & fixes (3-5 bullets)
- Add a `deterministic` option to `--engine` so the CLI matches the spec interface while continuing to default to the local assembler `docs/labs_spec.md:57-61`; `labs/cli.py:85-88`
- Extend external generator tests to assert mock-mode calls never emit Authorization headers, complementing the existing live-mode coverage `docs/labs_spec.md:204-205`; `tests/test_external_generator.py:114-143`
- Add normalization tests that feed extra keys and confirm `_canonicalize_asset` drops them before MCP validation `docs/labs_spec.md:118-125`; `labs/generator/external.py:609-633`; `tests/test_external_generator.py:231-257`

## Alignment with labs_spec.md (table: Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| --- | --- | --- |
| Generator assembles canonical sections with pruned controls | Present | `labs/generator/assembler.py:44-90`; `tests/test_generator_assembler.py:21-37` |
| Seeded determinism for assembler IDs | Present | `labs/generator/assembler.py:94-102`; `tests/test_determinism.py:10-27` |
| MCP endpoint defaults to TCP on unset/invalid values | Present | `labs/mcp_stdio.py:134-143`; `tests/test_tcp.py:140-176` |
| Strict vs relaxed modes still invoke MCP validation | Present | `labs/agents/critic.py:101-182`; `tests/test_pipeline.py:248-296` |
| `external.jsonl` captures transport, raw_response hash/size, provenance, and failure detail | Present | `labs/generator/external.py:294-333`; `tests/test_external_generator.py:43-98`; `tests/test_pipeline.py:229-238` |
| External live calls enforce Authorization headers, env keys, size guards, and taxonomy | Present | `labs/generator/external.py:161-515`; `tests/test_external_generator.py:114-229` |
| CLI exposes `--seed/--temperature/--timeout-s/--strict` controls | Present | `labs/cli.py:89-135`; `tests/test_pipeline.py:248-298` |
| CLI accepts `--engine=deterministic` alias | Divergent | `docs/labs_spec.md:57-61`; `labs/cli.py:85-88` |
| Normalization rejects unknown keys (verified) | Missing | `docs/labs_spec.md:118-125`; `labs/generator/external.py:609-633`; `tests/test_external_generator.py:231-257` |
| Mock-mode external runs omit Authorization headers (verified) | Missing | `docs/labs_spec.md:204-205`; `tests/test_external_generator.py:114-143` |

## Generator implementation (table: Component → Status → Evidence)
| Component | Status | Evidence |
| --- | --- | --- |
| AssetAssembler wiring & control pruning | Present | `labs/generator/assembler.py:44-118`; `tests/test_generator_assembler.py:21-37` |
| Seeded determinism & provenance injection | Present | `labs/generator/assembler.py:94-102`; `labs/agents/generator.py:61-86`; `tests/test_determinism.py:10-27` |
| Generator logs include trace/mode/transport/strict metadata | Present | `labs/agents/generator.py:80-145`; `tests/test_generator.py:11-81` |
| Experiment records capture validation outcome and failure reason/detail | Present | `labs/agents/generator.py:89-145`; `tests/test_generator.py:43-81` |

## Critic implementation (table: Responsibility → Status → Evidence)
| Responsibility | Status | Evidence |
| --- | --- | --- |
| Required field validation & issue reporting | Present | `labs/agents/critic.py:61-77`; `tests/test_critic.py:1-44` |
| Strict vs relaxed MCP handling (shared invocation) | Present | `labs/agents/critic.py:101-182`; `tests/test_critic.py:161-184` |
| Socket transport failure surfaces `socket_unavailable` detail | Present | `labs/agents/critic.py:86-100`; `tests/test_critic.py:187-200` |
| Review logs include trace/mode/transport/strict & taxonomy detail | Present | `labs/agents/critic.py:164-188`; `tests/test_pipeline.py:219-238` |

## Assembler / Wiring step (bullets: parameter index, dangling reference pruning, provenance)
- Collects `parameter_index` from shader/tone/haptic sections and prunes dangling controls before emitting assets `labs/generator/assembler.py:64-118`; `tests/test_generator_assembler.py:21-37`
- Deterministic IDs/timestamps derive from seed and feed provenance metadata for reproducibility `labs/generator/assembler.py:94-102`; `tests/test_determinism.py:10-27`
- Provenance embeds assembler agent/version and seed across both top-level and meta blocks `labs/generator/assembler.py:70-87`; `labs/agents/generator.py:61-86`

## Patch lifecycle (bullets: preview, apply, rate stubs, logging)
- Preview/apply/rate commands include trace_id, strict/mode flags, and transport provenance in JSONL logs `labs/patches.py:55-156`; `tests/test_patches.py:11-88`
- Apply handoffs reuse CriticAgent reviews so MCP validation and failure taxonomy are captured in patch logs `labs/patches.py:88-118`; `tests/test_patches.py:31-63`
- Rating stubs persist critic outcomes and propagate strict/transport metadata for RLHF loops `labs/patches.py:121-156`; `tests/test_patches.py:65-92`

## MCP integration (bullets: STDIO, TCP-default, socket-optional validation; failure handling; strict vs relaxed mode; 1 MiB caps; reason/detail logging; resolver fallback)
- Resolver defaults to TCP when `MCP_ENDPOINT` is unset/invalid and is unit-tested for both unset and bogus values `labs/mcp_stdio.py:134-143`; `tests/test_tcp.py:140-176`
- STDIO builder enforces `MCP_ADAPTER_CMD`, normalizes deprecated `SYN_SCHEMAS_DIR`, and warns once per process `labs/mcp_stdio.py:150-168`; `tests/test_critic.py:203-216`
- Socket transport requires `MCP_SOCKET_PATH` and failures surface `socket_unavailable` in critic reviews `labs/mcp_stdio.py:171-180`; `tests/test_critic.py:187-200`
- TCP and socket validators both enforce 1 MiB payload caps via shared transport helpers `labs/mcp_stdio.py:145-199`; `tests/test_tcp.py:130-159`; `tests/test_socket.py:37-88`
- Critic strict vs relaxed modes continue invoking MCP but downgrade outages when `LABS_FAIL_FAST=0` as required `labs/agents/critic.py:101-182`; `tests/test_critic.py:161-184`

## External generator integration (bullets: Gemini/OpenAI interface, provenance logging, CLI flags, error handling, MCP-enforced validation)
- Gemini/OpenAI subclasses share normalization, provenance injection, and schema defaults derived from the assembler baseline `labs/generator/external.py:538-672`; `tests/test_external_generator.py:19-61`
- Live mode obtains API keys/endpoints from env, injects Authorization headers, redacts them in logs, and persists attempt traces with hashes/sizes `labs/generator/external.py:118-349`; `tests/test_external_generator.py:114-143`
- Failure handling classifies taxonomy (`auth_error`, `rate_limited`, `bad_response`, `timeout`, `server_error`, `network_error`) and logs attempt history `labs/generator/external.py:161-292`; `tests/test_external_generator.py:64-229`
- CLI `--engine` path reuses CriticAgent + MCP validation so external assets follow the same gating before persistence `labs/cli.py:115-183`; `tests/test_pipeline.py:219-244`

## External generation LIVE (v0.3.4) (bullets: env keys, endpoint resolution, Authorization headers, timeout, retry/backoff, size guards, redaction, normalization → schema-valid)
- Env variables (`GEMINI_API_KEY`, `OPENAI_API_KEY`, endpoints, models, LABS_EXTERNAL_LIVE) drive live-mode resolution with defaults and mocks off by default `labs/generator/external.py:118-208`; `.example.env:18-26`
- Authorization headers emit only in live mode and are redacted in logs; tests confirm both header injection and redaction behaviour `labs/generator/external.py:447-465`; `tests/test_external_generator.py:114-143`
- Timeout/backoff honour base 200 ms exponential growth with jitter and stop on non-retryable taxonomies `labs/generator/external.py:161-258`; `tests/test_external_generator.py:186-229`
- Request bodies reject >256 KiB and responses reject >1 MiB prior to parsing `labs/generator/external.py:165-205`; `labs/generator/external.py:474-515`; `tests/test_external_generator.py:145-184`
- Normalization fills required sections, injects provenance under `asset.meta`, prunes unknown keys, and restores required control mappings `labs/generator/external.py:538-673`; `tests/test_external_generator.py:231-257`

## Test coverage (table: Feature → Tested? → Evidence, including socket failure coverage, resolver fallback, header injection, size caps, retry taxonomy)
| Feature | Tested? | Evidence |
| --- | --- | --- |
| Generator → Critic pipeline persists validated asset | Yes | `tests/test_pipeline.py:203-244` |
| MCP TCP default & resolver fallback | Yes | `tests/test_tcp.py:140-176` |
| Critic surfaces `socket_unavailable` detail when path missing | Yes | `tests/test_critic.py:187-200` |
| External header injection & redaction in live mode | Yes | `tests/test_external_generator.py:114-143` |
| External request/response size caps (256 KiB / 1 MiB) | Yes | `tests/test_external_generator.py:145-184` |
| Retry taxonomy (`auth_error` no retry, `rate_limited` retries) | Yes | `tests/test_external_generator.py:186-229` |
| Mock-mode external run omits Authorization headers | No | `docs/labs_spec.md:204-205`; `tests/test_external_generator.py:19-61` |
| Normalization rejects unknown keys | No | `docs/labs_spec.md:118-125`; `labs/generator/external.py:609-633`; `tests/test_external_generator.py:231-257` |

## Dependencies and runtime (table: Package → Used in → Required/Optional)
| Package | Used in | Required/Optional |
| --- | --- | --- |
| `pytest` | Test suite execution | Optional (dev/test) `requirements.txt:1` |

## Environment variables (bullets: name, default, transport defaults, behavior when MCP/external API unreachable, deprecated knobs)
- `MCP_ENDPOINT` selects STDIO/socket/TCP, defaulting to TCP when unset or invalid `labs/mcp_stdio.py:134-143`
- `MCP_HOST`/`MCP_PORT` configure TCP targets and are required when endpoint resolves to TCP `labs/mcp_stdio.py:183-199`
- `MCP_ADAPTER_CMD` plus optional `SYN_SCHEMAS_DIR` covers STDIO adapters with a single deprecation warning `labs/mcp_stdio.py:150-168`; `tests/test_critic.py:203-216`
- `MCP_SOCKET_PATH` is mandatory for socket transport; missing values raise `socket_unavailable` `labs/mcp_stdio.py:171-180`; `tests/test_critic.py:187-200`
- `LABS_FAIL_FAST` toggles strict/relaxed critic behaviour and defaults to strict when unset `labs/agents/critic.py:18-29`
- `LABS_EXPERIMENTS_DIR` directs where validated assets persist `labs/cli.py:20-47`
- `LABS_EXTERNAL_LIVE`, provider keys, endpoints, and models drive live external generators `labs/generator/external.py:118-208`; `.example.env:18-26`
- `LABS_SOCKET_TESTS` guards Unix socket coverage for sandboxed environments `tests/test_socket.py:12`
- `SYN_SCHEMAS_DIR` remains deprecated and only influences STDIO adapters when supplied `labs/mcp_stdio.py:158-167`

## Logging (bullets: structured JSONL, provenance fields, patch/rating/external fields, reason/detail on transport failures, location under meta/output/)
- `log_jsonl` ensures JSONL output under `meta/output/labs/` with timestamp enrichment for external entries `labs/logging.py:10-35`
- Generator, critic, and patch logs include trace IDs, strict flags, mode, transport, and validation failure taxonomy `labs/agents/generator.py:80-145`; `labs/agents/critic.py:164-188`; `labs/patches.py:55-156`; `tests/test_patches.py:11-88`
- External generator logs persist request parameters, redacted headers, raw_response hash/size, normalized assets, MCP results, provenance, and failure reason/detail `labs/generator/external.py:294-349`; `tests/test_external_generator.py:43-98`; `tests/test_pipeline.py:229-238`

## Documentation accuracy (bullets: README vs. labs_spec.md; TCP as default, socket optional; maintainer docs reference resolver; env cleanup; v0.3.4 setup for API keys/live mode)
- README highlights TCP default, socket optional, CLI external engines, and live-mode env setup matching the spec `README.md:68-92`; `docs/labs_spec.md:64-112`
- `.example.env` lists LABS_FAIL_FAST, LABS_EXTERNAL_LIVE, and provider endpoints/keys per requirements `docs/labs_spec.md:64-84`; `.example.env:1-26`
- Maintainer docs cite the transport resolver to prevent future drift `docs/process.md:31-46`
- `docs/troubleshooting_external.md` documents taxonomy reasons, env toggles, and redaction guidance `docs/troubleshooting_external.md:1-18`; `docs/labs_spec.md:179-198`

## Detected divergences
- CLI restricts `--engine` choices to `gemini|openai`, omitting the spec-listed `deterministic` alias `docs/labs_spec.md:57-61`; `labs/cli.py:85-88`

## Recommendations
- Add a `deterministic` option to `labs.cli` argument parsing and extend CLI tests to cover the explicit alias `docs/labs_spec.md:57-61`; `labs/cli.py:85-135`; `tests/test_pipeline.py:248-298`
- Introduce an external generator test that asserts mock-mode runs leave `request_headers` empty, ensuring secrets never leak when live mode is disabled `docs/labs_spec.md:204-205`; `labs/generator/external.py:188-245`; `tests/test_external_generator.py:19-143`
- Add a normalization test that supplies unsupported keys and verifies `_canonicalize_asset` drops them before MCP review `docs/labs_spec.md:118-125`; `labs/generator/external.py:609-633`; `tests/test_external_generator.py:231-257`
