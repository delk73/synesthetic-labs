## Summary of repo state
- Core generator→critic pipeline, MCP transports, and external engines match v0.3.4 expectations with strong unit + CLI coverage.
- Live external flows gate on env keys, enforce size caps/backoff, and log provenance-rich attempts across success/failure paths.
- Logging, patch lifecycle, and maintainer docs remain aligned with the spec; only minor provenance/logging naming gaps remain.

## Top gaps & fixes (3-5 bullets)
- Inject `api_version` into `asset.meta_info.provenance` so provenance matches the spec payload. (`labs/generator/external.py:980-992`)
- Rename or alias the provenance URL field to `api_endpoint` to align with the spec contract. (`labs/generator/external.py:982`; `docs/labs_spec.md:131-142`)
- Always emit a `failure` field (null on success) in `external.jsonl` records to satisfy the logging schema. (`labs/generator/external.py:309-339`; `docs/labs_spec.md:160-176`)

## Alignment with labs_spec.md (table: Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| --- | --- | --- |
| Live external API calls (Gemini/OpenAI) | Present | `labs/generator/external.py:118-515`, `tests/test_external_generator.py:117-176` |
| Mock mode default when live flag unset | Present | `labs/generator/external.py:82-91` |
| Normalize → schema-valid asset, reject unknown keys | Present | `labs/generator/external.py:639-727`, `tests/test_external_generator.py:302-327` |
| Pre-flight numeric bounds before MCP | Present | `labs/generator/external.py:730-765`, `tests/test_external_generator.py:330-365` |
| MCP validation invoked strict & relaxed | Present | `labs/agents/critic.py:85-188`, `tests/test_pipeline.py:190-228` |
| CLI flags (`--engine`, `--seed`, `--temperature`, `--timeout-s`, mode toggles) | Present | `labs/cli.py:82-128`, `tests/test_pipeline.py:203-260` |
| TCP default + resolver fallback | Present | `labs/mcp_stdio.py:162-170`, `tests/test_tcp.py:175-188` |
| 1 MiB transport cap enforcement | Present | `labs/transport.py:7-60`, `tests/test_tcp.py:122-138` |
| external.jsonl logging schema (trace/mode/transport/provenance) | Present | `labs/generator/external.py:309-339`, `tests/test_external_generator.py:43-63` |
| Provenance payload includes api_version/api_endpoint | Divergent | `docs/labs_spec.md:131-144`, `labs/generator/external.py:980-1019` |
| external.jsonl failure field populated or null | Divergent | `docs/labs_spec.md:160-176`, `labs/generator/external.py:309-337` |
| Secret redaction in logs | Present | `labs/generator/external.py:449-456`, `tests/test_external_generator.py:117-173` |
| Error taxonomy + retry policy | Present | `labs/generator/external.py:240-289`, `tests/test_external_generator.py:221-263` |
| Maintainer docs reference transport resolver | Present | `docs/process.md:41-45` |

## Generator implementation (table: Component → Status → Evidence)
| Component | Status | Evidence |
| --- | --- | --- |
| AssetAssembler wiring | Present | `labs/generator/assembler.py:21-116`, `tests/test_generator_assembler.py:12-43` |
| Deterministic IDs/timestamps | Present | `labs/generator/assembler.py:78-100` |
| Parameter index collection | Present | `labs/generator/assembler.py:108-122` |
| Control pruning | Present | `labs/generator/assembler.py:124-144` |
| GeneratorAgent logging & experiment records | Present | `labs/agents/generator.py:30-145`, `tests/test_generator.py:11-66` |

## Critic implementation (table: Responsibility → Status → Evidence)
| Responsibility | Status | Evidence |
| --- | --- | --- |
| Required-field checks | Present | `labs/agents/critic.py:71-82` |
| MCP bridge + outage handling | Present | `labs/agents/critic.py:96-170`, `tests/test_critic.py:55-159` |
| Strict vs relaxed downgrade | Present | `labs/agents/critic.py:61-69`, `tests/test_critic.py:162-185` |
| Structured logging of reviews | Present | `labs/agents/critic.py:182-188`, `tests/test_critic.py:25-98` |
| Rating stubs with trace metadata | Present | `labs/agents/critic.py:190-217`, `tests/test_ratings.py:7-30` |

## Assembler / Wiring step (bullets: parameter index, dangling reference pruning, provenance)
- `parameter_index` collects shader/tone/haptic parameters and sorts them for the asset. (`labs/generator/assembler.py:108-145`)
- Control mappings drop dangling references that do not match the parameter index. (`labs/generator/assembler.py:124-144`)
- Provenance records deterministic IDs/timestamps on seeded runs and seeds meta provenance. (`labs/generator/assembler.py:68-107`)

## Patch lifecycle (bullets: preview, apply, rate stubs, logging)
- `preview_patch` logs preview metadata with trace/mode/transport. (`labs/patches.py:47-74`, `tests/test_patches.py:13-36`)
- `apply_patch` merges updates, invokes the critic, and logs validation results. (`labs/patches.py:77-126`, `tests/test_patches.py:38-77`)
- `rate_patch` records RLHF stubs and links critic rating entries. (`labs/patches.py:129-161`, `tests/test_patches.py:79-114`)
- All actions append JSONL under `meta/output/labs/patches.jsonl`. (`labs/patches.py:47-161`)

## MCP integration (bullets)
- STDIO/TCP/Socket builders respect env configuration and share the TCP fallback default. (`labs/mcp_stdio.py:162-214`)
- Transport helpers enforce 1 MiB caps and classify oversize errors. (`labs/transport.py:7-71`, `tests/test_tcp.py:120-138`)
- Critic surfaces detailed `mcp_unavailable` vs `mcp_error` payloads with strict/relaxed behavior. (`labs/agents/critic.py:96-170`, `tests/test_critic.py:55-200`)
- Resolver fallback is unit-tested for unset/invalid endpoints. (`tests/test_tcp.py:175-188`, `tests/test_mcp.py:9-24`)

## External generator integration (bullets)
- Gemini/OpenAI subclasses share retry/backoff, mock plumbing, and normalization hooks. (`labs/generator/external.py:545-1217`)
- CLI dispatch persists assets only after MCP-reviewed success and records runs. (`labs/cli.py:115-170`, `tests/test_pipeline.py:229-260`)
- Logs capture parameters, redacted headers, raw response hash/size, and MCP results. (`labs/generator/external.py:309-339`, `tests/test_external_generator.py:43-100`)

## External generation LIVE (v0.3.4) (bullets)
- Env gating requires `LABS_EXTERNAL_LIVE` plus provider keys before sending real HTTP. (`labs/generator/external.py:82-115`, `tests/test_external_generator.py:117-147`)
- Endpoint resolution prefers env overrides with provider-specific defaults. (`labs/generator/external.py:438-456`)
- Authorization headers added in live mode and redacted in logs. (`labs/generator/external.py:449-456`, `tests/test_external_generator.py:117-145`)
- Exponential backoff with jitter honors taxonomy (no retry on auth/bad_response). (`labs/generator/external.py:200-264`, `tests/test_external_generator.py:221-263`)
- Request/response size guards enforce 256 KiB / 1 MiB limits. (`labs/generator/external.py:170-214`, `tests/test_external_generator.py:180-218`)
- Normalization fills defaults and enforces bounds. (`labs/generator/external.py:545-638`, `tests/test_external_generator.py:266-365`)
- Provenance missing `api_version`/`api_endpoint` naming remains divergent. (`labs/generator/external.py:980-1019`)

## Test coverage (table: Feature → Tested? → Evidence)
| Feature | Tested? | Evidence |
| --- | --- | --- |
| Critic socket failure detail (`socket_unavailable`) | Yes | `tests/test_critic.py:188-201` |
| Resolver fallback to TCP | Yes | `tests/test_tcp.py:175-188` |
| Header injection + redaction (live vs mock) | Yes | `tests/test_external_generator.py:117-173` |
| Request/response size caps | Yes | `tests/test_external_generator.py:180-218` |
| Retry taxonomy (no retry on auth, retry on 429) | Yes | `tests/test_external_generator.py:221-263` |
| Normalization defaults + rejection paths | Yes | `tests/test_external_generator.py:266-365` |
| CLI deterministic alias | Yes | `tests/test_pipeline.py:203-228` |

## Dependencies and runtime (table: Package → Used in → Required/Optional)
| Package | Used in | Required/Optional |
| --- | --- | --- |
| `jsonschema` | `mcp/validate.py:9-96` (MCP schema validation) | Required |
| `pytest` | `tests/` suite (e.g., `tests/test_external_generator.py:13`) | Optional (dev/test) |

## Environment variables (bullets)
- `MCP_ENDPOINT` defaults to TCP when unset/invalid; accepts `tcp|stdio|socket`. (`labs/mcp_stdio.py:162-170`; `.example.env:1-12`)
- `MCP_HOST` / `MCP_PORT` required for TCP validation. (`labs/mcp_stdio.py:197-214`)
- `MCP_ADAPTER_CMD` required for STDIO transport; honors deprecated `SYN_SCHEMAS_DIR` once with a warning. (`labs/mcp_stdio.py:178-196`)
- `MCP_SOCKET_PATH` required for socket transport and normalized via helper. (`labs/mcp_stdio.py:190-205`)
- `LABS_FAIL_FAST` toggles strict vs relaxed behavior across agents. (`labs/agents/critic.py:61-69`; `labs/generator/external.py:40-48`)
- `LABS_EXPERIMENTS_DIR` controls persistence location. (`labs/cli.py:34-49`; `.example.env:15-16`)
- `LABS_EXTERNAL_LIVE`, provider keys, endpoints, and model defaults drive external live mode. (`labs/generator/external.py:82-115`, `.example.env:18-25`)
- Deprecated `SYN_SCHEMAS_DIR` only applies to STDIO and emits a single warning. (`labs/mcp_stdio.py:180-188`, `tests/test_critic.py:204-217`)

## Logging (bullets)
- `log_jsonl` creates directories and appends ordered JSON lines for all agent streams. (`labs/logging.py:11-34`)
- Generator and critic agents log trace/mode/transport/strict metadata. (`labs/agents/generator.py:112-145`; `labs/agents/critic.py:182-212`)
- Patch lifecycle logs preview/apply/rate events with critic feedback. (`labs/patches.py:47-161`)
- External flows append to `meta/output/labs/external.jsonl` with redacted headers, raw response hash/size, and validation outcomes. (`labs/generator/external.py:309-355`; `tests/test_external_generator.py:43-100`)
- Divergence: `failure` key omitted on success; should be emitted as `null`. (`labs/generator/external.py:309-337`; `docs/labs_spec.md:160-176`)

## Documentation accuracy (bullets)
- README documents TCP defaults, socket optionality, external engines, and live-mode env setup. (`README.md:19-102`)
- Spec-required transport provenance guidance lives in the maintainer process guide. (`docs/process.md:41-45`)
- Troubleshooting doc mirrors error taxonomy for external engines. (`docs/troubleshooting_external.md:1-27`)
- `.example.env` lists transport + external variables with defaults/deprecation notes. (`.example.env:1-26`)

## Detected divergences
- `asset.meta_info.provenance` omits the `api_version` field and uses `endpoint` instead of the spec’s `api_endpoint`. (`labs/generator/external.py:980-1019`; `docs/labs_spec.md:131-142`)
- Successful `external.jsonl` entries skip the `failure` key instead of writing `null`, diverging from the spec schema. (`labs/generator/external.py:309-337`; `docs/labs_spec.md:160-176`)

## Recommendations
- Include `api_version` (defaulting to the subclass `api_version`) and rename or duplicate the URL key as `api_endpoint` in `meta_info.provenance`. (`labs/generator/external.py:980-1019`)
- When recording successful runs, add `"failure": null` so `external.jsonl` aligns with the documented schema. (`labs/generator/external.py:309-339`; `docs/labs_spec.md:160-176`)
- Extend external generator tests to assert the updated provenance fields and `failure` key to lock compliance once code changes land. (`tests/test_external_generator.py:43-365`)
