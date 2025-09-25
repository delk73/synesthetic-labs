## Summary of repo state
- Generator and assembler emit canonical sections, prune control targets, and stamp provenance for experiments (`labs/generator/assembler.py:64`; `labs/agents/generator.py:37`; `labs/agents/generator.py:64`).
- Critic enforces required keys, invokes MCP transports (STDIO/socket/TCP), and logs structured outcomes with fail-fast controls (`labs/agents/critic.py:46`; `labs/agents/critic.py:88`; `labs/agents/critic.py:160`).
- Patch lifecycle and CLI persist validated assets and lifecycle JSONL under `meta/output/labs/` (`labs/patches.py:26`; `labs/cli.py:107`; `labs/logging.py:10`).

## Top gaps & fixes (3-5 bullets)
- Enable Unix socket transport tests by default instead of module-wide skip so CI covers v0.2 requirements (`tests/test_socket.py:12`).
- Refresh the README introduction to reflect the v0.2-TCP scope rather than v0.2-only language (`README.md:3`).
- Either wire `SYN_EXAMPLES_DIR`/backend env vars into transports or trim them to avoid dead configuration (`.env:23`; `.env:28`; `docker-compose.yml:7`).

## Alignment with labs_spec.md (table: Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| --- | --- | --- |
| Generator includes modulation & rule bundle stubs | Present | `labs/generator/assembler.py:64`; `labs/experimental/modulation.py:45`; `labs/experimental/rule_bundle.py:55` |
| STDIO MCP validation via adapter | Present | `labs/mcp_stdio.py:134`; `tests/test_pipeline.py:111` |
| Unix socket transport & tests | Divergent | `labs/mcp_stdio.py:148`; `tests/test_socket.py:12` |
| TCP transport with deterministic errors | Present | `labs/mcp_stdio.py:159`; `labs/mcp/tcp_client.py:34`; `tests/test_tcp.py:66` |
| Patch lifecycle preview/apply/rate logging | Present | `labs/patches.py:26`; `tests/test_patches.py:43` |
| Critic rating stub logging | Present | `labs/agents/critic.py:170`; `tests/test_ratings.py:10` |
| Path traversal guard | Present | `labs/core.py:12`; `tests/test_path_guard.py:16` |
| Container runs as non-root | Present | `Dockerfile:3` |
| Docs describe STDIO/socket/TCP usage | Divergent | `README.md:3`; `README.md:29`; `docs/labs_spec.md:113` |

## Generator implementation (table: Component → Status → Evidence)
| Component | Status | Evidence |
| --- | --- | --- |
| AssetAssembler parameter index & pruning | Present | `labs/generator/assembler.py:64`; `labs/generator/assembler.py:114`; `tests/test_generator_assembler.py:18` |
| ShaderGenerator | Present | `labs/generator/shader.py:93`; `tests/test_generator_components.py:33` |
| ToneGenerator | Present | `labs/generator/tone.py:64`; `tests/test_generator_components.py:24` |
| HapticGenerator | Present | `labs/generator/haptic.py:44`; `tests/test_generator_components.py:28` |
| ControlGenerator | Present | `labs/generator/control.py:35`; `tests/test_generator_components.py:41` |
| MetaGenerator | Present | `labs/generator/meta.py:17`; `tests/test_generator_components.py:53` |
| Modulation stub integration | Present | `labs/experimental/modulation.py:45`; `tests/test_generator_assembler.py:32` |
| Rule bundle stub integration | Present | `labs/experimental/rule_bundle.py:55`; `tests/test_generator_assembler.py:34` |

## Critic implementation (table: Responsibility → Status → Evidence)
| Responsibility | Status | Evidence |
| --- | --- | --- |
| Required key checks & issue collection | Present | `labs/agents/critic.py:58`; `tests/test_critic.py:18` |
| MCP invocation & structured errors | Present | `labs/agents/critic.py:88`; `labs/agents/critic.py:70`; `tests/test_critic.py:92` |
| Fail-fast vs relaxed mode | Present | `labs/agents/critic.py:63`; `tests/test_pipeline.py:151` |
| Patch-aware review metadata | Present | `labs/agents/critic.py:157`; `tests/test_patches.py:43` |
| Rating stub logging | Present | `labs/agents/critic.py:170`; `tests/test_ratings.py:10` |

## Assembler / Wiring step (bullets: parameter index, dangling reference pruning, provenance)
- Parameter index gathers shader/tone/haptic parameters for controls (`labs/generator/assembler.py:104`).
- `_prune_controls` drops mappings not in the parameter index before persistence (`labs/generator/assembler.py:114`).
- Provenance embeds assembler/generator metadata with timestamps and seed tracking (`labs/generator/assembler.py:75`; `labs/agents/generator.py:50`).

## Patch lifecycle (bullets: preview, apply, rate stubs, logging)
- Preview logs intended updates without mutating the asset (`labs/patches.py:26`).
- Apply merges updates, invokes the critic, and records review payloads (`labs/patches.py:54`; `tests/test_patches.py:43`).
- Rate delegates to the critic’s rating stub and preserves linkage (`labs/patches.py:78`; `tests/test_patches.py:59`).
- All lifecycle actions append JSONL entries under `meta/output/labs/patches.jsonl` (`labs/patches.py:64`).

## MCP integration (bullets: STDIO, socket, and TCP validation; failure handling; strict vs relaxed mode)
- STDIO validator launches `MCP_ADAPTER_CMD` with normalized schema paths (`labs/mcp_stdio.py:134`).
- Socket validator enforces AF_UNIX framing and payload caps (`labs/mcp_stdio.py:148`; `labs/mcp/socket_main.py:20`).
- TCP validator reuses framing and surfaces connection errors deterministically (`labs/mcp_stdio.py:159`; `labs/mcp/tcp_client.py:34`).
- Critic maps outages to `validation_error.reason/detail` for observability (`labs/agents/critic.py:70`).
- `LABS_FAIL_FAST` toggles between failing and warning when MCP is unreachable (`labs/agents/critic.py:63`; `labs/cli.py:58`).

## Test coverage (table: Feature → Tested? → Evidence)
| Feature | Tested? | Evidence |
| --- | --- | --- |
| Generator determinism & wiring | Yes | `tests/test_determinism.py:8`; `tests/test_generator_assembler.py:18` |
| Component generators | Yes | `tests/test_generator_components.py:19` |
| Critic fail-fast vs relaxed | Yes | `tests/test_critic.py:92`; `tests/test_pipeline.py:151` |
| CLI generate/critique persistence | Yes | `tests/test_pipeline.py:92` |
| Patch lifecycle preview/apply/rate | Yes | `tests/test_patches.py:11`; `tests/test_patches.py:54` |
| Rating stub logging | Yes | `tests/test_ratings.py:10` |
| Prompt experiment batching | Yes | `tests/test_prompt_experiment.py:17` |
| Unix socket transport | Partial (skipped by default) | `tests/test_socket.py:12`; `tests/test_socket.py:33` |
| TCP transport round-trip & caps | Yes | `tests/test_tcp.py:66`; `tests/test_tcp.py:110` |

## Dependencies and runtime (table: Package → Used in → Required/Optional)
| Package | Used in | Required/Optional |
| --- | --- | --- |
| pytest | Test suite execution | Required (`requirements.txt:1`; `.github/workflows/ci.yml:18`) |
| Python standard library (argparse/json/socket/etc.) | CLI, transports, agents | Required (`labs/cli.py:5`; `labs/mcp_stdio.py:5`) |

## Environment variables (bullets: name, default, behavior when MCP unreachable)
- `MCP_ENDPOINT` (defaults to `stdio`) selects transport branch and raises `MCPUnavailableError` for unsupported values (`labs/mcp_stdio.py:132`; `labs/mcp_stdio.py:181`).
- `MCP_ADAPTER_CMD` is mandatory for STDIO; missing command triggers fail-fast errors (`labs/mcp_stdio.py:135`; `tests/test_critic.py:85`).
- `MCP_SOCKET_PATH` required for socket mode and normalized against traversal (`labs/mcp_stdio.py:148`; `labs/core.py:12`).
- `MCP_HOST`/`MCP_PORT` required for TCP; invalid or unreachable hosts report connection errors (`labs/mcp_stdio.py:159`; `labs/mcp/tcp_client.py:34`; `tests/test_tcp.py:134`).
- `LABS_FAIL_FAST` defaults to strict and decides whether MCP outages fail or are logged as skipped (`labs/agents/critic.py:24`; `labs/agents/critic.py:93`; `tests/test_pipeline.py:151`).
- `LABS_EXPERIMENTS_DIR` controls where validated assets persist when reviews pass (`labs/cli.py:19`; `labs/cli.py:112`).
- `SYN_SCHEMAS_DIR` forwarded to STDIO adapters after normalization (`labs/mcp_stdio.py:141`).
- `LABS_SOCKET_TESTS` gate keeps socket transport tests and currently disables them by default (`tests/test_socket.py:12`).
- `SYN_EXAMPLES_DIR`, `SYN_BACKEND_URL`, `SYN_BACKEND_ASSETS_PATH` are declared in the sample env and docker-compose but lack matching runtime handlers (`.env:23`; `.env:28`; `docker-compose.yml:7`).

## Logging (bullets: structured JSONL, provenance fields, patch/rating fields, location under meta/output/)
- `log_jsonl` ensures newline-delimited JSON and creates target directories (`labs/logging.py:10`).
- Generator logs both assets and experiment linkages to `meta/output/labs/generator.jsonl` (`labs/agents/generator.py:60`; `labs/agents/generator.py:98`).
- Critic logs reviews and rating stubs with validation metadata (`labs/agents/critic.py:160`; `labs/agents/critic.py:185`).
- Patch lifecycle writes preview/apply/rate events, embedding critic reviews and ratings (`labs/patches.py:64`; `tests/test_patches.py:49`).
- Prompt experiments append aggregated results per run for traceability (`labs/experiments/prompt_experiment.py:96`).

## Documentation accuracy (bullets: README vs. labs_spec.md)
- README intro still highlights "v0.2" scope despite TCP additions (`README.md:3`).
- README configuration section documents STDIO, socket, and TCP workflows correctly (`README.md:29`).
- `docs/labs_spec.md` v0.2-TCP section matches implemented transports and logging expectations (`docs/labs_spec.md:113`).

## Detected divergences
- Socket transport coverage depends on `LABS_SOCKET_TESTS` and is skipped in default runs, reducing assurance for v0.2 requirements (`tests/test_socket.py:12`).
- README messaging lags behind the v0.2-TCP scope, risking confusion about TCP availability (`README.md:3`).
- Environment sample includes unused schema/backend variables, introducing configuration drift (`.env:23`; `.env:28`).

## Recommendations
- Run Unix socket transport tests unconditionally in CI (or feature-detect support) to satisfy spec coverage (`tests/test_socket.py:12`).
- Update README copy to advertise v0.2-TCP capabilities alongside existing transport setup instructions (`README.md:3`; `README.md:29`).
- Remove or integrate the unused `SYN_EXAMPLES_DIR`/backend variables to align configuration with runtime behavior (`.env:23`; `.env:28`; `docker-compose.yml:7`).
