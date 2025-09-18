## Summary of repo state
- Generator enforces non-empty prompts, stamps UUID/timestamps, and logs proposals to JSONL via shared helper (`labs/agents/generator.py:29`, `labs/logging.py:17`, `tests/test_generator.py:22`)
- Critic records missing fields and MCP payloads yet leaves reviews `ok=True` when validation is skipped, violating fail-fast expectations (`labs/agents/critic.py:52`, `labs/agents/critic.py:72`, `docs/labs_spec.md:32`)
- CLI only wires MCP validation when env vars parse; otherwise it logs "validation skipped" and still executes the critique command successfully (`labs/cli.py:64`, `labs/cli.py:109`, `README.md:24`)
- Test suite covers generator and critic happy paths but omits failing MCP scenarios and any CLI assertions (`tests/test_critic.py:45`, `tests/test_pipeline.py:19`)

## Top gaps & fixes (3–5 bullets)
- Treat missing or unreachable MCP validators as hard failures in `CriticAgent.review` to satisfy the fail-fast spec (`docs/labs_spec.md:32`, `labs/agents/critic.py:52`)
- Propagate MCP configuration/connection failures through the CLI with a non-zero exit to avoid silent skips (`labs/cli.py:64`, `labs/cli.py:112`)
- Extend tests to assert the new failure semantics for both the critic and CLI surfaces (`tests/test_critic.py:45`, `tests/test_pipeline.py:19`)
- Update README once failure handling is enforced so instructions match observable behavior (`README.md:24`)

## Alignment with labs_spec.md and init.json (Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| --- | --- | --- |
| Generator logs provenance-tagged proposals to `meta/output` | Present | `labs/agents/generator.py:29`, `labs/logging.py:17`, `tests/test_generator.py:22` |
| Critic captures MCP responses on success | Present | `labs/agents/critic.py:58`, `labs/agents/critic.py:75`, `tests/test_pipeline.py:19` |
| Critic fails clearly when MCP unavailable | Missing | `docs/labs_spec.md:32`, `labs/agents/critic.py:52`, `tests/test_critic.py:45` |
| Critic logs "validation skipped" when MCP unreachable | Present | `meta/prompts/init.json:22`, `labs/agents/critic.py:56` |
| CLI requires MCP configuration before critiques proceed | Missing | `docs/labs_spec.md:32`, `labs/cli.py:64`, `labs/cli.py:109` |
| Structured JSONL logging stored under `meta/output/` | Present | `labs/logging.py:17`, `labs/agents/generator.py:52`, `labs/agents/critic.py:85` |
| Repo skeleton retains lifecycle/ and datasets scaffolds | Present | `meta/prompts/init.json:28`, `labs/lifecycle/__init__.py:1`, `labs/datasets/__init__.py:1` |
| Containerized test harness available | Present | `docs/labs_spec.md:53`, `Dockerfile:1`, `test.sh:4` |
| README documents MCP behavior accurately | Divergent | `README.md:24`, `docs/labs_spec.md:32`, `labs/cli.py:109` |
| Backlog tracks v0.2 follow-ons | Present | `docs/labs_spec.md:69`, `meta/backlog.md:3` |

## Test coverage (Feature → Tested? → Evidence)
| Feature | Tested? | Evidence |
| --- | --- | --- |
| Generator proposal logging & provenance | Yes | `tests/test_generator.py:22` |
| Critic required-field validation | Yes | `tests/test_critic.py:22` |
| Critic MCP success handoff | Yes | `tests/test_pipeline.py:19` |
| Critic fail-fast on MCP outage | No | `tests/test_critic.py:45` (asserts warning but not failure) |
| CLI critique failure propagation | No | _No CLI-focused tests; behavior only exercised via `labs/cli.py`_ |

## Dependencies and runtime (Package → Used in → Required/Optional)
| Package | Used in | Required/Optional |
| --- | --- | --- |
| pytest | Test suite (`tests/*.py`, CI) | Required (`requirements.txt:1`, `tests/test_generator.py:1`)

## Environment variables
- `MCP_HOST` (default `localhost`, `.env.example:1`): when unset, `_build_validator` logs a skip and critiques run without MCP enforcement, yielding `ok=True` reviews (`labs/cli.py:64`, `labs/agents/critic.py:72`)
- `MCP_PORT` (default `7000`, `.env.example:2`): invalid or missing values make `_build_validator` return `None`, leaving critiques to proceed without validation (`labs/cli.py:71`, `labs/cli.py:74`)
- `SYN_SCHEMAS_DIR` (default empty, `.env.example:3`): absence triggers another skip message and prevents validator construction (`labs/cli.py:77`, `labs/cli.py:80`)
- `SYN_EXAMPLES_DIR` (default empty, `.env.example:4`): exported for container parity yet currently unused by the codebase (`docker-compose.yml:7`, `docker-compose.yml:10`)
- Unreachable MCP adapter: `SocketMCPValidator.validate` raises `MCPUnavailableError`, but the critic downgrades this to a skipped validation and still reports success (`labs/cli.py:33`, `labs/agents/critic.py:62`, `labs/agents/critic.py:72`)

## Documentation accuracy (README vs. labs_spec.md)
- README promises the CLI exits on MCP outages, but the implementation merely logs and continues (`README.md:24`, `labs/cli.py:64`)
- README references MCP requirements without clarifying that current code does not enforce them, diverging from the fail-fast mandate (`README.md:24`, `docs/labs_spec.md:32`)

## Detected divergences
- Critic allows skipped validation to count as success instead of failing fast as mandated (`labs/agents/critic.py:52`, `docs/labs_spec.md:32`)
- CLI accepts missing MCP configuration and still returns a successful critique, contradicting documentation and spec intent (`labs/cli.py:64`, `README.md:24`)

## Recommendations
- Change `CriticAgent.review` to mark `ok=False` (or raise) when validation is skipped so runs fail when MCP is unavailable (`labs/agents/critic.py:52`, `docs/labs_spec.md:32`)
- Make the CLI exit with a non-zero status whenever `_build_validator` returns `None` or the validator raises `MCPUnavailableError` to surface outages (`labs/cli.py:64`, `labs/cli.py:112`)
- Add unit/integration tests that assert fail-fast behavior for both the critic and CLI critique command to lock in the new contract (`tests/test_critic.py:45`, `tests/test_pipeline.py:19`)
- Revise README instructions after enforcing failure semantics so user guidance reflects actual behavior (`README.md:24`, `labs/cli.py:109`)
