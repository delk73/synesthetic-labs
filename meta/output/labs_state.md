## Summary of repo state
- Generator proposal flow logs UUID/timestamped payloads to JSONL via shared logging helper, matching spec expectations (`labs/agents/generator.py:29`, `labs/logging.py:12`)
- Critic reviews capture issues and MCP responses but still mark `ok=True` when validation is skipped, so MCP outages do not surface as failures (`labs/agents/critic.py:52`, `tests/test_critic.py:45`)
- CLI only injects MCP validation when env vars are set; otherwise it logs "validation skipped" and continues without enforcing failure (`labs/cli.py:64`, `labs/cli.py:109`)
- Pytest suite covers generator, critic, and pipeline handoff but omits CLI behavior and failing MCP scenarios (`tests/test_generator.py:10`, `tests/test_critic.py:45`, `tests/test_pipeline.py:9`)

## Top gaps & fixes (3–5 bullets)
- Set `ok=False` and surface a clear failure when MCP validation is skipped or unreachable to satisfy the fail-fast requirement (`labs/agents/critic.py:52`, `tests/test_critic.py:45`)
- Make the CLI exit non-zero when `_build_validator` cannot configure MCP access or when the validator raises `MCPUnavailableError` (`labs/cli.py:64`, `labs/cli.py:112`)
- Update tests to assert the new failure semantics, including CLI coverage for unreachable MCP adapters (`tests/test_critic.py:45`, `tests/test_pipeline.py:9`)
- Correct README instructions so they match the enforced MCP failure behavior once implemented (`README.md:24`)

## Alignment with labs_spec.md and init.json (Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| --- | --- | --- |
| Generator agent produces proposals with provenance and logs to meta/output | Present | `labs/agents/generator.py:29`, `labs/logging.py:12`, `tests/test_generator.py:10` |
| Critic agent fails clearly when MCP unavailable | Missing | `labs/agents/critic.py:52`, `tests/test_critic.py:45`, `docs/labs_spec.md:32` |
| Critic logs MCP responses when validation succeeds | Present | `labs/agents/critic.py:58`, `tests/test_pipeline.py:19` |
| Generator → critic handoff wired with MCP validation hook | Present | `tests/test_pipeline.py:9`, `labs/agents/critic.py:58` |
| Structured JSONL logging under meta/output | Present | `labs/logging.py:12`, `labs/agents/critic.py:84`, `labs/agents/generator.py:52` |
| CLI requires MCP configuration and fails fast when unavailable | Missing | `labs/cli.py:64`, `labs/cli.py:109`, `docs/labs_spec.md:32` |
| README documents MCP fallback expectations from init.json | Divergent | `README.md:24`, `meta/prompts/init.json:18`, `docs/labs_spec.md:32` |
| Repo skeleton includes lifecycle/ and datasets/ scaffolds | Present | `labs/lifecycle/__init__.py:1`, `labs/datasets/__init__.py:1` |
| Backlog tracked for v0.2 items | Present | `meta/backlog.md:1` |

## Test coverage (Feature → Tested? → Evidence)
| Feature | Tested? | Evidence |
| --- | --- | --- |
| Generator proposal logging and provenance | Yes | `tests/test_generator.py:10` |
| Critic required-field validation | Yes | `tests/test_critic.py:22` |
| Critic handling of MCP unavailable | Partial | `tests/test_critic.py:45` (asserts warning but not failure) |
| Critic MCP success payload persistence | Yes | `tests/test_pipeline.py:16` |
| CLI critique command MCP failure path | No | _Not covered_ |

## Dependencies and runtime (Package → Used in → Required/Optional)
| Package | Used in | Required/Optional |
| --- | --- | --- |
| pytest | `tests/*.py`, CI workflow | Required for test harness (`requirements.txt:1`, `.github/workflows/ci.yml:15`) |

## Environment variables
- `MCP_HOST` (default `localhost` via `.env.example:1`): when unset, `_build_validator` logs "validation skipped" and returns `None`, allowing critiques to run without MCP failure (`labs/cli.py:64`)
- `MCP_PORT` (default `7000` via `.env.example:2`): invalid or missing values trigger a warning and skip validation, still leaving reviews `ok=True` (`labs/cli.py:67`, `labs/agents/critic.py:52`)
- `SYN_SCHEMAS_DIR` (default empty via `.env.example:3`): absence causes validator setup to be skipped with an info log, no failure surfaced to the user (`labs/cli.py:77`)
- `SYN_EXAMPLES_DIR` (default empty via `.env.example:4`): provided for parity with containers but currently unused in code paths (`docker-compose.yml:9`)
- Unreachable MCP adapter: `SocketMCPValidator.validate` raises `MCPUnavailableError`, yet `CriticAgent.review` catches it and still reports `ok=True`, masking outages (`labs/cli.py:33`, `labs/agents/critic.py:62`)

## Documentation accuracy (README vs. labs_spec.md)
- README claims the CLI exits with an error when MCP is unreachable, but current implementation only logs and proceeds, conflicting with spec requirements (`README.md:24`, `labs/cli.py:64`)
- README does not mention the need to fail fast despite the spec mandating clear failures on MCP outages (`README.md:24`, `docs/labs_spec.md:32`)

## Detected divergences
- Critic success criteria diverge from the spec: reviews remain `ok=True` when validation is skipped rather than failing fast (`labs/agents/critic.py:52`, `docs/labs_spec.md:32`)
- CLI behavior diverges from documented expectations, silently accepting missing MCP configuration (`labs/cli.py:64`, `README.md:24`)

## Recommendations
- Update `CriticAgent.review` to treat skipped validation as a failure (set `ok=False`, capture an issue message) so MCP downtime surfaces immediately (`labs/agents/critic.py:52`)
- Propagate validation failures through the CLI by exiting non-zero when `_build_validator` returns `None` or when the validator raises `MCPUnavailableError` (`labs/cli.py:64`, `labs/cli.py:112`)
- Extend tests to cover CLI critique failure paths and assert that skipped validation now fails (`tests/test_critic.py:45`, `tests/test_pipeline.py:9`)
- Revise README guidance after enforcing fail-fast behavior to accurately describe the CLI requirements (`README.md:24`)
