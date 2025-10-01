# Synesthetic Labs State (v0.3.3 Audit)

## Summary of repo state
- Generator->critic pipeline handles local and external paths, persists validated assets, and records experiments via JSONL logs (labs/cli.py:108; labs/cli.py:131; labs/agents/generator.py:37; tests/test_pipeline.py:93; tests/test_pipeline.py:211).
- MCP transports default to TCP while supporting STDIO and socket with 1 MiB caps and transport-specific reason/detail logging (labs/mcp_stdio.py:129; labs/mcp_stdio.py:145; labs/transport.py:8; labs/agents/critic.py:70; tests/test_tcp.py:140; tests/test_critic.py:186).
- Structured logging covers generator, critic, patch lifecycle, and external runs under meta/output/labs/ (labs/logging.py:13; labs/agents/generator.py:61; labs/patches.py:57; labs/generator/external.py:168; tests/test_patches.py:26; tests/test_external_generator.py:16).
- Spec-mandated env cleanup is incomplete because SYN_SCHEMAS_DIR remains in code, samples, and tooling (docs/labs_spec.md:184; labs/mcp_stdio.py:152; .env:22; .example.env:13; e2e.sh:9; docker-compose.yml:5; README.md:47).

## Top gaps & fixes (3-5 bullets)
- Remove SYN_SCHEMAS_DIR handling from the validator builder to align with the v0.3.3 environment cleanup requirement (docs/labs_spec.md:184; labs/mcp_stdio.py:152).
- Prune the deprecated SYN_SCHEMAS_DIR variable from .env, .example.env, and README so samples match the spec (docs/labs_spec.md:184; .env:22; .example.env:13; README.md:47).
- Update operational scripts and compose files to stop exporting SYN_SCHEMAS_DIR (docs/labs_spec.md:184; e2e.sh:9; docker-compose.yml:5).

## Alignment with labs_spec.md
| Spec item | Status | Evidence |
| --- | --- | --- |
| TCP default transport | Present | labs/mcp_stdio.py:129; tests/test_tcp.py:163 |
| STDIO/TCP/socket validators from env | Present | labs/mcp_stdio.py:145; labs/mcp_stdio.py:159; labs/mcp_stdio.py:170 |
| MCP validation runs in strict & relaxed modes | Present | labs/agents/critic.py:63; labs/cli.py:59; tests/test_pipeline.py:63 |
| Failure logs include reason/detail | Present | labs/agents/critic.py:70; tests/test_critic.py:55 |
| External generator provenance logged with MCP result | Present | labs/generator/external.py:168; tests/test_pipeline.py:211 |
| Socket transport optional/documented | Present | tests/test_socket.py:9; README.md:57 |
| Critic socket failure detail covered by tests | Present | tests/test_critic.py:186 |
| resolve_mcp_endpoint fallback tested | Present | labs/mcp_stdio.py:129; tests/test_tcp.py:163; tests/test_tcp.py:171 |
| Maintainer docs reference resolver fallback | Present | README.md:45 |
| Environment cleanup removes SYN_SCHEMAS_DIR | Divergent | docs/labs_spec.md:184; labs/mcp_stdio.py:152; .env:22; .example.env:13; e2e.sh:9; docker-compose.yml:5 |

## Generator implementation
| Component | Status | Evidence |
| --- | --- | --- |
| AssetAssembler | Present | labs/generator/assembler.py:44 |
| ShaderGenerator | Present | labs/generator/shader.py:87 |
| ToneGenerator | Present | labs/generator/tone.py:58 |
| HapticGenerator | Present | labs/generator/haptic.py:38 |
| ControlGenerator | Present | labs/generator/control.py:35 |
| MetaGenerator | Present | labs/generator/meta.py:14 |
| ModulationGenerator | Present | labs/experimental/modulation.py:45 |
| RuleBundleGenerator | Present | labs/experimental/rule_bundle.py:52 |

## Critic implementation
| Responsibility | Status | Evidence |
| --- | --- | --- |
| Required field checks | Present | labs/agents/critic.py:58 |
| MCP validation (strict/relaxed) | Present | labs/agents/critic.py:63; tests/test_pipeline.py:63 |
| Transport provenance detail | Present | labs/agents/critic.py:68; tests/test_critic.py:55 |
| Review JSONL logging | Present | labs/agents/critic.py:148; labs/logging.py:13 |
| Rating stub logging | Present | labs/agents/critic.py:170; tests/test_patches.py:49 |

## Assembler / Wiring step
- Parameter index aggregates shader, tone, and haptic inputs for downstream wiring (labs/generator/assembler.py:64; labs/generator/assembler.py:105).
- Control mappings are pruned to avoid dangling references (labs/generator/assembler.py:66; labs/generator/assembler.py:118).
- Provenance stamps assembler and generator metadata, including deterministic IDs when seeds are provided (labs/generator/assembler.py:70; labs/generator/assembler.py:75; labs/agents/generator.py:50).

## Patch lifecycle
- Preview logs patch changes without mutating the asset (labs/patches.py:18; tests/test_patches.py:7).
- Apply merges updates, routes through CriticAgent, and logs the review payload (labs/patches.py:37; tests/test_patches.py:26).
- Rate records critic rating stubs and lifecycle entries (labs/patches.py:68; labs/agents/critic.py:170; tests/test_patches.py:49).

## MCP integration
- TCP is the default transport and STDIO/socket validators are constructed from env overrides when requested (labs/mcp_stdio.py:129; labs/mcp_stdio.py:145; labs/mcp_stdio.py:159; labs/mcp_stdio.py:170; tests/test_tcp.py:140).
- Critic surfaces MCP outages with structured reason/detail fields per transport (labs/agents/critic.py:70; labs/agents/critic.py:116; tests/test_critic.py:55; tests/test_critic.py:186).
- Strict (fail-fast) and relaxed modes both invoke MCP validation while adjusting severity (labs/agents/critic.py:63; labs/cli.py:59; tests/test_pipeline.py:63; tests/test_pipeline.py:152).
- Transport helpers enforce a 1 MiB payload cap and propagate oversize failures (labs/transport.py:8; labs/transport.py:53; tests/test_tcp.py:110; tests/test_socket.py:26).
- Resolver fallback to TCP is verified for unset and invalid settings (labs/mcp_stdio.py:129; tests/test_tcp.py:163; tests/test_tcp.py:171).

## External generator integration
- Gemini and OpenAI generators share retry/backoff, mock mode, and provenance injection with trace IDs (labs/generator/external.py:74; labs/generator/external.py:315; labs/generator/external.py:347; labs/generator/external.py:397).
- CLI generate command routes external engines through CriticAgent and asset persistence (labs/cli.py:108; labs/cli.py:141; tests/test_pipeline.py:211).
- Successful runs log MCP results and provenance to meta/output/labs/external.jsonl (labs/generator/external.py:168; tests/test_pipeline.py:221).
- Failures capture attempt traces with structured reason/detail metadata (labs/generator/external.py:189; labs/generator/external.py:200; tests/test_external_generator.py:52).

## Test coverage
| Feature | Tested? | Evidence |
| --- | --- | --- |
| Asset determinism | Yes | tests/test_determinism.py:8 |
| Generator->critic pipeline | Yes | tests/test_pipeline.py:15 |
| CLI relaxed mode warns but continues | Yes | tests/test_pipeline.py:63 |
| CLI generate --engine flow | Yes | tests/test_pipeline.py:211 |
| External failure logging | Yes | tests/test_external_generator.py:52 |
| Patch lifecycle logging | Yes | tests/test_patches.py:7 |
| TCP oversize/error handling | Yes | tests/test_tcp.py:110 |
| Critic socket failure detail | Yes | tests/test_critic.py:186 |
| resolve_mcp_endpoint fallback | Yes | tests/test_tcp.py:163; tests/test_tcp.py:171 |
| Socket transport round trip (guarded) | Yes (guarded) | tests/test_socket.py:9 |

## Dependencies and runtime
| Package | Used in | Required/Optional |
| --- | --- | --- |
| pytest | Test runner invoked by CI (`pytest -q`) (requirements.txt:1; .github/workflows/ci.yml:11) | Required |

## Environment variables
- MCP_ENDPOINT defaults to "tcp" and accepts stdio/socket/tcp, falling back to TCP for invalid values (labs/mcp_stdio.py:132; labs/mcp_stdio.py:135).
- MCP_HOST and MCP_PORT are required when using TCP transport (labs/mcp_stdio.py:170; labs/mcp_stdio.py:174).
- MCP_ADAPTER_CMD must be set for STDIO adapters (labs/mcp_stdio.py:145; labs/mcp_stdio.py:148).
- MCP_SOCKET_PATH is mandatory for socket transport configuration (labs/mcp_stdio.py:159; labs/mcp_stdio.py:163).
- LABS_FAIL_FAST toggles strict vs relaxed severity while still invoking MCP (labs/agents/critic.py:21; labs/agents/critic.py:118; tests/test_pipeline.py:63).
- LABS_EXPERIMENTS_DIR overrides the persisted asset directory (labs/cli.py:34; labs/cli.py:45; tests/test_pipeline.py:93).
- LABS_EXTERNAL_LIVE controls mock vs live external generation (labs/generator/external.py:61; labs/generator/external.py:67).
- GEMINI_MODEL sets the Gemini model identifier (labs/generator/external.py:347).
- OPENAI_MODEL and OPENAI_TEMPERATURE configure OpenAI parameters (labs/generator/external.py:397; labs/generator/external.py:400).
- LABS_SOCKET_TESTS enables optional Unix socket tests (tests/test_socket.py:9).
- SYN_SCHEMAS_DIR is still forwarded to STDIO adapters despite the v0.3.3 cleanup requirement (labs/mcp_stdio.py:152; .env:22; .example.env:13).

## Logging
- log_jsonl creates parent directories and appends sorted JSON lines (labs/logging.py:13; labs/logging.py:25).
- GeneratorAgent logs assets and experiment metadata to meta/output/labs/generator.jsonl (labs/agents/generator.py:61; labs/agents/generator.py:98).
- CriticAgent records reviews and rating stubs with validation_error details (labs/agents/critic.py:148; labs/agents/critic.py:170).
- Patch lifecycle appends preview/apply/rate events to meta/output/labs/patches.jsonl (labs/patches.py:18; labs/patches.py:57; labs/patches.py:68).
- External generators log successful validations and API failures to meta/output/labs/external.jsonl (labs/generator/external.py:168; labs/generator/external.py:200).

## Documentation accuracy
- README documents TCP as the default transport with automatic fallback (README.md:45).
- README notes Unix socket tests are optional via LABS_SOCKET_TESTS (README.md:57).
- README continues to mention the deprecated SYN_SCHEMAS_DIR knob, conflicting with the cleanup requirement (README.md:47; docs/labs_spec.md:184).
- labs_spec.md captures resolver fallback expectations for maintainers (docs/labs_spec.md:182; docs/labs_spec.md:189).

## Detected divergences
- SYN_SCHEMAS_DIR remains supported and documented even though v0.3.3 requires its removal from docs and samples (docs/labs_spec.md:184; labs/mcp_stdio.py:152; .env:22; .example.env:13; e2e.sh:9; docker-compose.yml:5; README.md:47).

## Recommendations
- Drop SYN_SCHEMAS_DIR forwarding from build_validator_from_env and rely on MCP-managed schema lookup (docs/labs_spec.md:184; labs/mcp_stdio.py:152).
- Remove the deprecated variable from env templates and README to keep samples compliant (docs/labs_spec.md:184; .env:22; .example.env:13; README.md:47).
- Update e2e.sh and docker-compose.yml to run without exporting SYN_SCHEMAS_DIR (docs/labs_spec.md:184; e2e.sh:9; docker-compose.yml:5).
