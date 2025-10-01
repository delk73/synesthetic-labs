# Synesthetic Labs State (v0.3.3 Audit)

## Summary of repo state
- Generator → critic pipeline stays deterministic with persisted experiments and CLI coverage for preview/apply/rate/external engines (labs/agents/generator.py:37-104; labs/cli.py:82-210).
- MCP transports support STDIO, TCP-by-default, and optional socket with shared 1 MiB guards plus provenance-aware error reporting (labs/mcp_stdio.py:129-190; labs/transport.py:9-47; labs/agents/critic.py:68-166).
- Audit-driven gaps remain around resolver fallback tests, critic socket failure coverage, and doc/env cleanup mandated by v0.3.3 (docs/labs_spec.md:182-191; tests/test_critic.py:23-182; .example.env:13).

## Top gaps & fixes (3-5 bullets)
- Add a critic socket failure test that asserts the `socket_unavailable` detail to satisfy the v0.3.3 coverage requirement (docs/labs_spec.md:182; labs/agents/critic.py:68-138; tests/test_critic.py:23-182).
- Write direct unit tests for `resolve_mcp_endpoint` covering unset and invalid `MCP_ENDPOINT` values so fallback behaviour is locked down (docs/labs_spec.md:182; labs/mcp_stdio.py:129-137; tests/test_tcp.py:140-160).
- Update README and `.example.env` to document resolver fallback and remove or clearly deprecate `SYN_SCHEMAS_DIR` per the spec cleanup (docs/labs_spec.md:183-191; README.md:45-56; .example.env:13).

## Alignment with labs_spec.md
| Spec item | Status | Evidence |
| --- | --- | --- |
| TCP default transport | Present | labs/mcp_stdio.py:129-137 |
| STDIO/TCP/socket validators from env | Present | labs/mcp_stdio.py:145-190 |
| MCP validation runs in strict & relaxed modes | Present | labs/agents/critic.py:63-138; tests/test_critic.py:160-182 |
| Failure logs include reason/detail | Present | labs/agents/critic.py:68-138 |
| External generator runs log provenance + MCP result | Present | labs/generator/external.py:168-223; tests/test_pipeline.py:211-227 |
| Socket transport optional/documented | Present | tests/test_socket.py:9-63; README.md:55 |
| Critic socket failure detail covered by tests | Missing | docs/labs_spec.md:182; tests/test_critic.py:23-182 |
| `resolve_mcp_endpoint` fallback tested | Missing | docs/labs_spec.md:182; tests/test_tcp.py:140-160 |
| Maintainer docs reference resolver fallback | Missing | docs/labs_spec.md:183-191; README.md:45-56 |
| Environment cleanup removes `SYN_SCHEMAS_DIR` | Divergent | docs/labs_spec.md:184; .example.env:13; labs/mcp_stdio.py:152-154 |

## Generator implementation
| Component | Status | Evidence |
| --- | --- | --- |
| AssetAssembler | Present | labs/generator/assembler.py:20-92 |
| ShaderGenerator | Present | labs/generator/shader.py:1-75 |
| ToneGenerator | Present | labs/generator/tone.py:1-80 |
| HapticGenerator | Present | labs/generator/haptic.py:1-58 |
| ControlGenerator | Present | labs/generator/control.py:1-38 |
| MetaGenerator | Present | labs/generator/meta.py:1-22 |
| ModulationGenerator | Present | labs/experimental/modulation.py:1-40 |
| RuleBundleGenerator | Present | labs/experimental/rule_bundle.py:1-47 |

## Critic implementation
| Responsibility | Status | Evidence |
| --- | --- | --- |
| Required field checks | Present | labs/agents/critic.py:58-62 |
| MCP validation (strict/relaxed) | Present | labs/agents/critic.py:63-138; tests/test_pipeline.py:63-186 |
| Transport provenance in errors | Present | labs/agents/critic.py:68-84 |
| Review JSONL logging | Present | labs/agents/critic.py:148-168 |
| Rating stub logging | Present | labs/agents/critic.py:170-192; tests/test_patches.py:49-57 |

## Assembler / Wiring step
- Parameter index aggregates shader/tone/haptic inputs for downstream wiring (labs/generator/assembler.py:64-112).
- Control mappings are pruned to the collected parameters to avoid dangling references (labs/generator/assembler.py:66-123).
- Provenance stamps assembler + generator metadata with deterministic IDs/timestamps (labs/generator/assembler.py:50-90; labs/agents/generator.py:48-58).

## Patch lifecycle
- Preview logs patch changes without mutating the asset (labs/patches.py:19-36; tests/test_patches.py:7-24).
- Apply merges updates, routes through the critic, and logs the review payload (labs/patches.py:38-65; tests/test_patches.py:26-47).
- Rate captures critic rating stubs and appends lifecycle entries (labs/patches.py:67-83; tests/test_patches.py:49-57).

## MCP integration
- STDIO/TCP/socket validators share the builder with TCP as the default and socket optional (labs/mcp_stdio.py:129-190; tests/test_socket.py:9-63).
- Fail-fast vs relaxed mode still invokes MCP while adjusting severity (labs/agents/critic.py:63-138; tests/test_pipeline.py:63-186).
- Structured reason/detail surfaces for MCP outages and schema errors (labs/agents/critic.py:68-140; tests/test_critic.py:55-157).
- 1 MiB payload caps enforced across transports (labs/transport.py:9-47; tests/test_tcp.py:110-137; tests/test_socket.py:26-59).
- Resolver fallback logic defaults invalid/unset endpoints to TCP but lacks explicit tests (labs/mcp_stdio.py:129-137; tests/test_tcp.py:140-160).

## External generator integration
- Gemini/OpenAI generators share retry/backoff and provenance injection (labs/generator/external.py:27-223; tests/test_external_generator.py:16-82).
- CLI `--engine` runs persist MCP-reviewed assets and external logs (labs/cli.py:108-164; tests/test_pipeline.py:191-229).
- Failures capture attempt traces with `failure.reason/detail` (labs/generator/external.py:189-223; tests/test_external_generator.py:52-82).
- Mock mode defaults ensure MCP validation precedes persistence even when live transports are disabled (labs/generator/external.py:61-124; labs/cli.py:131-152).

## Test coverage
| Feature | Tested? | Evidence |
| --- | --- | --- |
| Asset determinism | Yes | tests/test_determinism.py:6-20 |
| Generator → critic pipeline | Yes | tests/test_pipeline.py:15-90 |
| CLI generate `--engine` path | Yes | tests/test_pipeline.py:191-229 |
| External failure logging | Yes | tests/test_external_generator.py:52-82 |
| Patch lifecycle logging | Yes | tests/test_patches.py:7-57 |
| TCP validator oversize/error handling | Yes | tests/test_tcp.py:110-137 |
| Socket transport round trip (guarded by `LABS_SOCKET_TESTS`) | Optional | tests/test_socket.py:9-63 |
| Critic socket failure detail | No | tests/test_critic.py:23-182 |
| `resolve_mcp_endpoint` fallback | No | tests/test_tcp.py:140-160 |

## Dependencies and runtime
| Package | Used in | Required/Optional |
| --- | --- | --- |
| pytest | Test suite execution (`pytest -q`) | Required (requirements.txt:1) |

## Environment variables
- `MCP_ENDPOINT`: defaults to TCP; accepts `stdio`/`socket`/`tcp`, invalid values fall back to TCP (labs/mcp_stdio.py:129-137).
- `MCP_HOST` / `MCP_PORT`: required for TCP validator construction (labs/mcp_stdio.py:170-189).
- `MCP_ADAPTER_CMD`: needed when running STDIO adapters (labs/mcp_stdio.py:145-157).
- `MCP_SOCKET_PATH`: mandatory for socket transport configuration (labs/mcp_stdio.py:159-168).
- `LABS_FAIL_FAST`: toggles strict vs relaxed severity while still invoking MCP (labs/agents/critic.py:21-138; tests/test_pipeline.py:63-186).
- `LABS_EXPERIMENTS_DIR`: overrides persisted asset location (labs/cli.py:20-49; tests/test_pipeline.py:93-138).
- `LABS_EXTERNAL_LIVE`: enables live external transports (labs/generator/external.py:61-68).
- `GEMINI_MODEL` / `OPENAI_MODEL` / `OPENAI_TEMPERATURE`: configure external request parameters (labs/generator/external.py:347-401).
- `LABS_SOCKET_TESTS`: guards optional Unix socket tests (tests/test_socket.py:9).
- `SYN_SCHEMAS_DIR`: still forwarded to STDIO adapters despite spec cleanup (labs/mcp_stdio.py:152-154; .example.env:13).

## Logging
- `log_jsonl` ensures directory creation and stable JSONL output (labs/logging.py:13-35).
- Generator agent logs assets and experiment records under `meta/output/labs/generator.jsonl` (labs/agents/generator.py:37-104; tests/test_pipeline.py:93-138).
- Critic reviews and rating stubs append structured entries with reason/detail (labs/agents/critic.py:148-192; tests/test_patches.py:49-57).
- Patch lifecycle appends preview/apply/rate events to `meta/output/labs/patches.jsonl` (labs/patches.py:19-83).
- External generator runs and failures stream to `meta/output/labs/external.jsonl` (labs/generator/external.py:168-223; tests/test_external_generator.py:16-82).

## Documentation accuracy
- README highlights TCP default and optional socket tests but omits resolver fallback guidance (README.md:45-56).
- labs_spec v0.3.3 enumerates required coverage, doc updates, and env cleanup (docs/labs_spec.md:182-191).
- Maintainer-facing docs still need explicit resolver fallback references (docs/labs_spec.md:183-191; README.md:45-56).
- `.example.env` retains `SYN_SCHEMAS_DIR` contrary to the cleanup exit criteria (docs/labs_spec.md:184; .example.env:13).

## Detected divergences
- `SYN_SCHEMAS_DIR` remains supported/documented even though v0.3.3 calls for removal from samples (docs/labs_spec.md:184; labs/mcp_stdio.py:152-154; .example.env:13).

## Recommendations
- Add a critic socket failure test that triggers `MCP_ENDPOINT=socket` and validates the `socket_unavailable` detail (docs/labs_spec.md:182; labs/agents/critic.py:68-138).
- Introduce unit coverage for `resolve_mcp_endpoint`, including invalid values falling back to TCP (labs/mcp_stdio.py:129-137; tests/test_tcp.py:140-160).
- Refresh README and env samples to describe resolver fallback and remove or mark `SYN_SCHEMAS_DIR` as deprecated (docs/labs_spec.md:183-191; README.md:45-56; .example.env:13).
