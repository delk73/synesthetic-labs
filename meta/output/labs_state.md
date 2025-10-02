# Synesthetic Labs State Audit (v0.3.4)

## Summary of repo state
The repository is in a good state and largely compliant with the v0.3.4 spec. The core feature, live external generator calls, is implemented with robust error handling, logging, and security considerations. TCP is correctly implemented as the default transport, and the fallback mechanism is in place. Test coverage for the new features is good, including header injection, size caps, and retry logic. However, there are a few minor divergences from the spec regarding normalization and pre-flight validation in the external generator path, and a missing CLI alias.

## Top gaps & fixes
- **Divergent: Normalization drops unknown keys.** The spec requires that the normalization step for external generator responses *rejects* payloads with unknown top-level keys. The current implementation silently drops them. This should be changed to raise a `bad_response` error. (File: `labs/generator/external.py`)
- **Missing: Pre-flight numeric bounds enforcement.** The spec requires that numeric bounds (like haptic intensity `[0,1]` and parameter `min`/`max`/`default` relationships) are validated *before* calling the MCP. This is currently not implemented. (File: `labs/generator/external.py`)
- **Missing: `deterministic` engine alias.** The CLI does not currently support `--engine=deterministic` as an alias for the default generator, which is specified in the v0.3.4 spec. (File: `labs/cli.py`)
- **Missing: Test for `resolve_mcp_endpoint` fallback.** While the logic exists, there is no dedicated unit test to confirm that `resolve_mcp_endpoint` correctly falls back to TCP when `MCP_ENDPOINT` is invalid or unset.

## Alignment with labs_spec.md (v0.3.4)

| Spec item | Status | Evidence |
|---|---|---|
| Live external API calls (Gemini/OpenAI) | Present | `labs/generator/external.py` |
| Mock mode by default | Present | `labs/generator/external.py:L118-L121` |
| Normalize external output to schema-valid asset | Divergent | `labs/generator/external.py:L538-L688` (Does not reject unknown keys) |
| Always run MCP validation | Present | `labs/cli.py:L153-L156` |
| `ExternalGenerator` protocol | Present | `docs/labs_spec.md` (Defined in spec, implemented in `labs/generator/external.py`) |
| CLI flags for external generators | Present | `labs/cli.py:L80-L96` |
| Environment variables authoritative list | Present | `.example.env`, `docs/labs_spec.md` |
| TCP as default transport | Present | `labs/mcp_stdio.py:L134-L139` |
| 1 MiB transport cap | Present | `labs/transport.py:L7-L13` |
| Request/Response mapping for external calls | Present | `labs/generator/external.py:L353-L383` |
| Normalization contract | Divergent | `labs/generator/external.py:L538-L688` (Missing numeric bounds checks and rejection of unknown keys) |
| Provenance injection | Present | `labs/generator/external.py:L582-L600` |
| Secret redaction | Present | `labs/generator/external.py:L450-L456` |
| Pre-flight validation | Missing | `labs/generator/external.py` (Numeric bounds not checked) |
| MCP validation in strict/relaxed modes | Present | `labs/cli.py:L153-L156`, `labs/agents/critic.py:L85-L188` |
| `external.jsonl` logging | Present | `labs/generator/external.py:L294-L349` |
| Error taxonomy and retry policy | Present | `labs/generator/external.py:L493-L537` |
| Security: Keys from env, no file access | Present | `labs/generator/external.py:L438-L444` |
| Unit tests for v0.3.4 features | Present | `tests/test_external_generator.py` |

## Generator implementation

| Component | Status | Evidence |
|---|---|---|
| `AssetAssembler` | Present | `labs/generator/assembler.py` |
| Deterministic ID/timestamp generation | Present | `labs/generator/assembler.py:L104-L112` |
| Parameter index collection | Present | `labs/generator/assembler.py:L114-L122` |
| Dangling control pruning | Present | `labs/generator/assembler.py:L124-L133` |
| `GeneratorAgent` | Present | `labs/agents/generator.py` |

## Critic implementation

| Responsibility | Status | Evidence |
|---|---|---|
| Review asset for required keys | Present | `labs/agents/critic.py:L75-L78` |
| Coordinate MCP validation | Present | `labs/agents/critic.py:L85-L188` |
| Handle fail-fast vs. relaxed modes | Present | `labs/agents/critic.py:L61-L69`, `labs/agents/critic.py:L88-L146` |
| Log review outcomes | Present | `labs/agents/critic.py:L186-L188` |
| Record rating stubs | Present | `labs/agents/critic.py:L190-L217` |

## Assembler / Wiring step
- **Parameter index:** Present and correct. `AssetAssembler._collect_parameters` gathers all `input_parameters` from shader, tone, and haptic sections. (`labs/generator/assembler.py:L114-L122`)
- **Dangling reference pruning:** Present and correct. `AssetAssembler._prune_controls` ensures that only `controls` that map to existing parameters in the `parameter_index` are included in the final asset. (`labs/generator/assembler.py:L124-L133`)
- **Provenance:** Present. The `AssetAssembler` injects deterministic provenance for seeded runs. (`labs/generator/assembler.py:L90-L97`)

## Patch lifecycle
- **Preview:** Present. `preview_patch` logs the intent to patch without modification. (`labs/patches.py:L47-L71`)
- **Apply:** Present. `apply_patch` applies the patch and invokes the `CriticAgent` for validation. (`labs/patches.py:L74-L126`)
- **Rate stubs:** Present. `rate_patch` logs a rating for a given patch. (`labs/patches.py:L129-L161`)
- **Logging:** Present. All lifecycle events are logged to `meta/output/labs/patches.jsonl`.

## MCP integration
- **STDIO, TCP-default, socket-optional validation:** Present. `resolve_mcp_endpoint` correctly defaults to TCP. `build_validator_from_env` constructs the correct validator based on the environment. (`labs/mcp_stdio.py:L134-L205`)
- **Failure handling:** Present. `CriticAgent` and `cli.py` handle `MCPUnavailableError` and log failures with reason/detail. (`labs/agents/critic.py:L107-L146`, `labs/cli.py:L154-L157`)
- **Strict vs relaxed mode:** Present. `is_fail_fast_enabled()` controls the behavior, and the critic downgrades errors to warnings in relaxed mode. (`labs/agents/critic.py:L61-L69`, `labs/agents/critic.py:L122-L129`)
- **1 MiB caps:** Present. `labs/transport.py` enforces the size limit on encode and decode.
- **Reason/detail logging:** Present. The `CriticAgent` constructs detailed error payloads on MCP failure. (`labs/agents/critic.py:L96-L106`)
- **Resolver fallback:** Present but untested. The logic in `resolve_mcp_endpoint` correctly falls back to `tcp`, but no specific unit test asserts this. (`labs/mcp_stdio.py:L134-L139`)

## External generator integration
- **Gemini/OpenAI interface:** Present. `GeminiGenerator` and `OpenAIGenerator` classes exist. (`labs/generator/external.py`)
- **Provenance logging:** Present. `_normalise_asset` injects a detailed provenance block. (`labs/generator/external.py:L582-L600`)
- **CLI flags:** Present. `--engine`, `--seed`, `--temperature`, `--timeout-s`, and `--strict`/`--relaxed` are all implemented. (`labs/cli.py:L80-L96`)
- **Error handling:** Present. `ExternalGenerationError` and `ExternalRequestError` are used to classify and handle errors. (`labs/generator/external.py`)
- **MCP-enforced validation:** Present. The CLI ensures that all generated assets are passed through the `CriticAgent`. (`labs/cli.py:L153-L156`)

## External generation LIVE (v0.3.4)
- **Env keys:** Present. `GEMINI_API_KEY` and `OPENAI_API_KEY` are read from the environment. (`labs/generator/external.py:L438-L444`)
- **Endpoint resolution:** Present. The generator resolves endpoints from environment variables or uses defaults. (`labs/generator/external.py:L445-L448`)
- **Authorization headers:** Present. `Authorization: Bearer <key>` is added in live mode. (`labs/generator/external.py:L449-L450`)
- **Timeout, retry/backoff:** Present. Implemented with exponential backoff and jitter. (`labs/generator/external.py:L160-L220`)
- **Size guards:** Present. 256KiB request and 1MiB response caps are enforced. (`labs/generator/external.py:L29-L30`, `tests/test_external_generator.py:L188-L220`)
- **Redaction:** Present. API keys are redacted in logs. (`labs/generator/external.py:L450-L456`)
- **Normalization → schema-valid:** Divergent. Normalization is implemented but fails to reject unknown keys or perform pre-flight numeric bounds checks as required by the spec. (`labs/generator/external.py:L538-L688`)

## Test coverage

| Feature | Tested? | Evidence |
|---|---|---|
| Critic socket failure coverage | Present | `tests/test_critic.py:L203-L217` asserts `socket_unavailable` detail. |
| Resolver fallback | Missing | No specific test for `resolve_mcp_endpoint` fallback on invalid `MCP_ENDPOINT` value. |
| Header injection (live vs mock) | Present | `tests/test_external_generator.py:L118-L173` |
| Size caps (request/response) | Present | `tests/test_external_generator.py:L188-L220` |
| Retry taxonomy (no-retry on auth) | Present | `tests/test_external_generator.py:L223-L237` |
| Normalization (defaults) | Present | `tests/test_external_generator.py:L263-L281` |
| Normalization (rejection) | Missing | No tests for rejection of unknown keys or out-of-bounds numerics. |

## Dependencies and runtime

| Package | Used in | Required/Optional |
|---|---|---|
| `pytest` | `tests/` | Required (for testing) |

The project has no runtime dependencies beyond the Python standard library.

## Environment variables
- **`MCP_ENDPOINT`**: `tcp` (default), `stdio`, `socket`. Fallback to `tcp` if invalid.
- **`MCP_HOST`**: `127.0.0.1` (default). Used for TCP transport.
- **`MCP_PORT`**: `8765` (default). Used for TCP transport.
- **`MCP_ADAPTER_CMD`**: No default. Required for `stdio` transport.
- **`MCP_SOCKET_PATH`**: No default. Required for `socket` transport.
- **`LABS_FAIL_FAST`**: `1` (default). Controls strict vs. relaxed validation.
- **`LABS_EXTERNAL_LIVE`**: `0` (default). Enables live API calls for external generators.
- **`GEMINI_API_KEY`**: No default. Required for live Gemini calls.
- **`OPENAI_API_KEY`**: No default. Required for live OpenAI calls.
- **`SYN_SCHEMAS_DIR`**: Deprecated. A warning is logged if used with the `stdio` adapter.

## Logging
- **Structured JSONL:** Present. All major components log to `.jsonl` files. (`labs/logging.py`)
- **Provenance fields:** Present. `trace_id`, `mode`, `strict`, `transport` are logged.
- **`external.jsonl`:** Present and matches spec. (`labs/generator/external.py:L294-L349`)
- **Reason/detail on transport failures:** Present. (`labs/agents/critic.py:L96-L106`)
- **Location:** `meta/output/labs/`

## Documentation accuracy
- **README vs. labs_spec.md:** Mostly aligned. The README accurately reflects TCP as the default, the optional nature of the socket transport, and the setup for v0.3.4 live mode.
- **Maintainer docs reference resolver:** Present. `docs/process.md` references `resolve_mcp_endpoint`.
- **Env cleanup:** The deprecated `SYN_SCHEMAS_DIR` is correctly documented in the README and `.example.env`.

## Detected divergences
1.  **Normalization Rejection:** `ExternalGenerator._canonicalize_asset` does not reject payloads with unknown top-level keys; it only processes known keys. The spec requires rejection.
2.  **Pre-flight Bounds Checking:** `ExternalGenerator._validate_bounds` is incomplete. It checks some bounds but not all required by the spec, and it should be called before MCP validation.
3.  **CLI Alias:** The `generate` command is missing the `--engine=deterministic` alias.

## Recommendations
1.  **Modify `ExternalGenerator._canonicalize_asset`:** Change the logic to identify and reject any keys in the input payload that are not part of the `allowed_keys` set, raising an `ExternalRequestError("bad_response", "unknown_key:...")`.
2.  **Implement `ExternalGenerator._validate_bounds`:** Complete the implementation of `_validate_bounds` to check haptic intensity and parameter min/max/default values, and ensure it is called from `_normalise_asset` before MCP validation. Add corresponding unit tests.
3.  **Update `labs/cli.py`:** Add `deterministic` to the `choices` tuple for the `--engine` argument and handle it as an alias for the default `GeneratorAgent`.
4.  **Add Test for Resolver Fallback:** Create a new unit test in `tests/test_critic.py` or `tests/test_tcp.py` that sets an invalid `MCP_ENDPOINT` and asserts that `resolve_mcp_endpoint()` returns `'tcp'`.