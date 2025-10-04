# Troubleshooting External Generators

The external Gemini/OpenAI integrations surface failures using the spec taxonomy. Use the table below to diagnose issues.

| Reason | Description | Suggested actions |
| --- | --- | --- |
| `auth_error` | Missing or rejected API key (`401`/`403`). | Confirm `GEMINI_API_KEY` or `OPENAI_API_KEY` is set; rotate secrets if revoked. |
| `rate_limited` | Provider throttled the request (`429`). | Back off, reduce frequency, or request higher quotas. |
| `timeout` | Client-side deadline expired. | Increase `--timeout-s`, check network health, or retry later. |
| `network_error` | Connection failed before a response. | Verify endpoint URL, firewall rules, or local proxy settings. |
| `server_error` | Provider returned a 5xx response. | Retry after backoff or escalate to provider support. |
| `bad_response` | Response exceeded size caps or failed schema normalization. | Inspect `raw_response.hash`/`detail`, tighten prompts, or escalate a bug fix. |

Additional tips:

- Live mode requires `LABS_EXTERNAL_LIVE=1` plus the relevant API key and endpoint variables in the environment.
- Sensitive headers (e.g., `Authorization`) are redacted in `meta/output/labs/external.jsonl`; use provider dashboards to audit live traffic.
- The CLI `--strict/--relaxed` flags map to `LABS_FAIL_FAST`. Use `--relaxed` during adapter outages to continue logging failures without persisting invalid assets.
