# Summary of repo state
- Generator pipeline still assembles canonical sections and prunes control mappings before logging proposals `labs/generator/assembler.py:64`; `tests/test_pipeline.py:15`
- Critic reviews enforce required fields, call MCP, and surface transport-specific validation errors `labs/agents/critic.py:63`; `tests/test_critic.py:187`
- MCP resolver defaults to TCP with exercised STDIO/socket branches and payload caps `labs/mcp_stdio.py:134`; `tests/test_tcp.py:110`
- External generators remain mock-focused; external.jsonl lacks transport/raw_response metadata required by the spec `labs/generator/external.py:170`; `tests/test_external_generator.py:36`
- v0.3.4 live-call requirements (Authorization headers, env keys, CLI toggles, troubleshooting doc) are absent `docs/labs_spec.md:60`; `labs/generator/external.py:275`; `labs/cli.py:82`; `docs/labs_spec.md:235`

# Top gaps & fixes (3-5 bullets)
- Implement env-driven API key handling, Authorization header injection, redaction, and raw_response hashing in external logs to meet the v0.3.4 logging contract `docs/labs_spec.md:108`; `docs/labs_spec.md:160`; `labs/generator/external.py:170`; `labs/generator/external.py:275`
- Extend CLI `generate` with `--seed`, `--temperature`, `--timeout-s`, and `--strict/--relaxed` plus precedence tests so MCP modes map correctly to LABS_FAIL_FAST `docs/labs_spec.md:60`; `labs/cli.py:82`; `tests/test_pipeline.py:178`
- Add trace_id, mode, transport, strict flag, and structured failure reason/detail to generator, critic, patch, and external logs `docs/labs_spec.md:155`; `labs/agents/generator.py:61`; `labs/agents/critic.py:148`; `labs/patches.py:57`
- Harden external normalization to fill required meta/controls defaults, reject unknown keys, and cover with schema-validation tests `docs/labs_spec.md:118`; `labs/generator/external.py:325`; `tests/test_external_generator.py:16`

# Alignment with labs_spec.md (table: Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| --- | --- | --- |
| Generator assembles canonical sections with pruned controls | Present | `labs/generator/assembler.py:64`; `tests/test_generator_assembler.py:32` |
| Seeded determinism for assembler IDs | Present | `labs/generator/assembler.py:94`; `tests/test_determinism.py:10` |
| MCP endpoint defaults to TCP on unset/invalid | Present | `labs/mcp_stdio.py:134`; `tests/test_tcp.py:163` |
| Strict vs relaxed still invokes MCP validation | Present | `labs/agents/critic.py:110`; `tests/test_pipeline.py:181` |
| external.jsonl includes transport, strict flag, raw_response hash, provenance block | Missing | `docs/labs_spec.md:160`; `labs/generator/external.py:170` |
| External live calls send Authorization header from env keys | Missing | `docs/labs_spec.md:108`; `labs/generator/external.py:275` |
| Retry/backoff honors taxonomy (no retry on auth/bad_response, exponential w/ jitter) | Divergent | `docs/labs_spec.md:189`; `labs/generator/external.py:142` |
| Normalization stores provenance under meta and enforces required defaults | Missing | `docs/labs_spec.md:118`; `labs/generator/external.py:311` |
| CLI exposes --seed/--temperature/--timeout-s/--strict flags | Missing | `docs/labs_spec.md:60`; `labs/cli.py:82` |
| README/.env document new live-call env vars & troubleshooting | Missing | `docs/labs_spec.md:235`; `.example.env:1`; `README.md:75` |

# Generator implementation (table: Component → Status → Evidence)
| Component | Status | Evidence |
| --- | --- | --- |
| AssetAssembler wiring & control pruning | Present | `labs/generator/assembler.py:64`; `tests/test_generator_assembler.py:32` |
| Seeded determinism & provenance injection | Present | `labs/generator/assembler.py:94`; `tests/test_generator.py:24` |
| Generator log entries include trace metadata per spec | Missing | `docs/labs_spec.md:155`; `labs/agents/generator.py:61` |
| Experiment records capture structured failure reason/detail | Divergent | `docs/labs_spec.md:155`; `labs/agents/generator.py:82` |

# Critic implementation (table: Responsibility → Status → Evidence)
| Responsibility | Status | Evidence |
| --- | --- | --- |
| Required field validation | Present | `labs/agents/critic.py:58`; `tests/test_critic.py:16` |
| Fail-fast vs relaxed behavior | Present | `labs/agents/critic.py:63`; `tests/test_critic.py:161` |
| Transport-specific reason/detail surfaced | Present | `labs/agents/critic.py:70`; `tests/test_critic.py:187` |
| Review logs include trace_id/mode/transport | Missing | `docs/labs_spec.md:155`; `labs/agents/critic.py:148` |
| Rating stub logging | Present | `labs/agents/critic.py:182`; `tests/test_ratings.py:10` |

# Assembler / Wiring step (bullets: parameter index, dangling reference pruning, provenance)
- Collects `parameter_index` from shader/tone/haptic sections for downstream controls `labs/generator/assembler.py:64`
- Prunes control mappings to drop dangling parameter references before persistence `labs/generator/assembler.py:115`
- Deterministic IDs/timestamps derive from seed and feed provenance metadata `labs/generator/assembler.py:94`; `tests/test_determinism.py:10`

# Patch lifecycle (bullets: preview, apply, rate stubs, logging)
- Preview logs patch diffs with timestamp but no trace metadata `labs/patches.py:26`; `tests/test_patches.py:11`
- Apply re-validates via CriticAgent and appends review payload lacking transport/strict flags `labs/patches.py:57`; `tests/test_patches.py:25`
- Rate delegates to CriticAgent rating stub and logs lifecycle entry without spec-required trace_id `labs/patches.py:81`; `tests/test_patches.py:44`

# MCP integration (bullets: STDIO, TCP-default, socket-optional validation; failure handling; strict vs relaxed mode; 1 MiB caps; reason/detail logging; resolver fallback)
- STDIO builder requires `MCP_ADAPTER_CMD`, normalizes deprecated `SYN_SCHEMAS_DIR`, and warns once `labs/mcp_stdio.py:150`; `tests/test_critic.py:203`
- TCP transport is the default fallback when endpoint unset/invalid, covered by tests `labs/mcp_stdio.py:134`; `tests/test_tcp.py:163`
- Socket transport optional with explicit unavailable detail captured when path missing `labs/mcp_stdio.py:171`; `tests/test_critic.py:187`
- MCP transports enforce 1 MiB payload caps via shared helpers `labs/transport.py:20`; `tests/test_tcp.py:110`
- Strict vs relaxed modes still attempt MCP, downgrading failures when LABS_FAIL_FAST=0 `labs/agents/critic.py:110`; `tests/test_pipeline.py:181`
- Validation errors log transport-specific reason/detail but logs omit trace metadata `labs/agents/critic.py:148`

# External generator integration (bullets: Gemini/OpenAI interface, provenance logging, CLI flags, error handling, MCP-enforced validation)
- Mock mode is default via `LABS_EXTERNAL_LIVE` guard and reuses critic validation path `labs/generator/external.py:61`; `tests/test_pipeline.py:191`
- Successful runs capture attempt traces and MCP results but omit transport/strict/raw_response fields `labs/generator/external.py:170`
- CLI only exposes `--engine` flag; no parameter/strict toggles yet `labs/cli.py:82`
- Retry/backoff logic is linear (`delay = backoff_seconds * attempt`) without taxonomy-aware aborts `labs/generator/external.py:142`
- Failure logging emits generic `api_failed` reason instead of spec taxonomy `labs/generator/external.py:214`

# External generation LIVE (v0.3.4) (bullets: env keys, endpoint resolution, Authorization headers, timeout, retry/backoff, size guards, redaction, normalization → schema-valid)
- Env keys `GEMINI_API_KEY`/`OPENAI_API_KEY` and endpoints are not wired; `.example.env` omits them `docs/labs_spec.md:76`; `.example.env:1`; `labs/generator/external.py:347`
- Live mode sends only `Content-Type` with no Authorization header or secret redaction `docs/labs_spec.md:108`; `labs/generator/external.py:275`
- Timeout/backoff do not match required connect/read splits or exponential jitter policy `docs/labs_spec.md:189`; `labs/generator/external.py:142`
- Request/response size guards (256 KiB / 1 MiB) are not enforced for external calls `docs/labs_spec.md:110`; `labs/generator/external.py:275`
- Normalization leaves placeholder sections, lacks required meta/controls defaults, and stores provenance outside `asset.meta` `docs/labs_spec.md:118`; `labs/generator/external.py:321`
- No documentation or tests cover live mode gating or endpoint resolution `docs/labs_spec.md:235`; `tests/test_external_generator.py:16`

# Test coverage (table: Feature → Tested? → Evidence, including socket failure coverage, resolver fallback, header injection, size caps, retry taxonomy)
| Feature | Tested? | Evidence |
| --- | --- | --- |
| Generator → Critic happy path persists validated asset | Yes | `tests/test_pipeline.py:15` |
| MCP TCP default & fallback behavior | Yes | `tests/test_tcp.py:150` |
| Socket transport surfaces `socket_unavailable` detail | Yes | `tests/test_critic.py:187` |
| External generator mock run logged with MCP result | Yes | `tests/test_pipeline.py:211` |
| Resolver invalid endpoint falls back to TCP | Yes | `tests/test_tcp.py:170` |
| Authorization header injection for live calls | No | `docs/labs_spec.md:204`; `tests/test_external_generator.py:16` |
| External request/response size caps (256 KiB / 1 MiB) | No | `docs/labs_spec.md:205`; `tests/test_external_generator.py:52` |
| Retry taxonomy (auth_error, rate_limited, timeout) handling | No | `docs/labs_spec.md:213`; `tests/test_external_generator.py:52` |
| Live mode smoke tests gated by LABS_EXTERNAL_LIVE | No | `docs/labs_spec.md:218`; `tests/test_external_generator.py:16` |

# Dependencies and runtime (table: Package → Used in → Required/Optional)
| Package | Used in | Required/Optional |
| --- | --- | --- |
| `pytest` | `tests/` suite execution | Optional (dev/test) `requirements.txt:1` |

# Environment variables (bullets: name, default, transport defaults, behavior when MCP/external API unreachable, deprecated knobs)
- `MCP_ENDPOINT` selects validator transport; defaults to `tcp` on unset/invalid `labs/mcp_stdio.py:134`
- `MCP_HOST`/`MCP_PORT` required for TCP connections `labs/mcp_stdio.py:183`
- `MCP_ADAPTER_CMD` required for STDIO adapter and `SYN_SCHEMAS_DIR` passes through with one-time warning `labs/mcp_stdio.py:150`; `labs/mcp_stdio.py:158`
- `MCP_SOCKET_PATH` mandatory for socket transport; missing path raises `socket_unavailable` `labs/mcp_stdio.py:171`; `tests/test_critic.py:187`
- `LABS_FAIL_FAST` defaults to strict (`True`) in critic logic `labs/agents/critic.py:18`
- `LABS_EXPERIMENTS_DIR` controls persistence directory for validated assets `labs/cli.py:20`
- `LABS_EXTERNAL_LIVE` toggles mock vs live but no API key enforcement yet `labs/generator/external.py:61`
- `GEMINI_MODEL`, `OPENAI_MODEL`, `OPENAI_TEMPERATURE` seed request parameters `labs/generator/external.py:347`; `labs/generator/external.py:371`
- `GEMINI_API_KEY` and `OPENAI_API_KEY` are spec-required but unused/undocumented `docs/labs_spec.md:76`; `.example.env:1`
- `LABS_SOCKET_TESTS` gates Unix socket tests `tests/test_socket.py:12`
- `SYN_SCHEMAS_DIR` deprecated STDIO-only override, warned once `labs/mcp_stdio.py:158`

# Logging (bullets: structured JSONL, provenance fields, patch/rating/external fields, reason/detail on transport failures, location under meta/output/)
- All agents use JSONL sinks under `meta/output/labs/` with directory auto-creation `labs/logging.py:10`
- Generator, critic, and patch records omit trace_id, resolved transport, and strict mode flags required by spec `docs/labs_spec.md:155`; `labs/agents/generator.py:61`; `labs/agents/critic.py:148`; `labs/patches.py:57`
- External logs capture request/response and MCP result but miss transport, raw_response hash, provenance block, and spec taxonomy `docs/labs_spec.md:160`; `labs/generator/external.py:170`
- Failure reasons use `validation_failed`/`api_failed` instead of enumerated auth/rate/timeout codes `labs/generator/external.py:190`; `labs/generator/external.py:218`

# Documentation accuracy (bullets: README vs. labs_spec.md; TCP as default, socket optional; maintainer docs reference resolver; env cleanup; v0.3.4 setup for API keys/live mode)
- README covers TCP default and socket optional transports but omits API key setup for live mode `README.md:71`; `docs/labs_spec.md:236`
- `.example.env` lacks new external variables and redaction guidance `docs/labs_spec.md:239`; `.example.env:1`
- Maintainer process highlights `resolve_mcp_endpoint` usage (aligned) `docs/process.md:41`
- `docs/troubleshooting_external.md` is absent despite spec requirement `docs/labs_spec.md:240`

# Detected divergences
- External retry/backoff uses linear delay without taxonomy-aware aborts `docs/labs_spec.md:189`; `labs/generator/external.py:142`
- External failure logging emits `api_failed` instead of spec-defined reasons `docs/labs_spec.md:181`; `labs/generator/external.py:218`
- External normalization stores provenance outside `asset.meta` and leaves placeholder sections `docs/labs_spec.md:118`; `labs/generator/external.py:321`
- Logging streams omit required trace_id/mode/transport metadata `docs/labs_spec.md:155`; `labs/agents/critic.py:148`

# Recommendations
- Build an HTTP client wrapper that loads provider API keys from env, injects Authorization headers, enforces 256 KiB/1 MiB size guards, applies exponential backoff with spec taxonomy, redacts secrets, and logs raw_response hash + transport fields `docs/labs_spec.md:108`; `docs/labs_spec.md:189`; `labs/generator/external.py:170`
- Extend `labs.cli generate` to accept seed/timeout/temperature and strict/relaxed flags, updating tests to cover CLI/env precedence and MCP invocation counts `docs/labs_spec.md:60`; `labs/cli.py:82`; `tests/test_pipeline.py:181`
- Augment generator/critic/patch logging payloads with trace_id, resolved transport, strict flag, and structured failure reason/detail, then backfill tests asserting the new metadata `docs/labs_spec.md:155`; `labs/agents/critic.py:148`; `tests/test_patches.py:25`
- Enforce external normalization defaults (meta fields, control mappings), reject unknown keys, and add schema validation tests plus README/.env documentation and troubleshooting guide updates `docs/labs_spec.md:118`; `docs/labs_spec.md:235`; `labs/generator/external.py:325`; `.example.env:1`
