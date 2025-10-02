---
version: v0.3.4
lastReviewed: 2025-10-02
owner: labs-core
---

# Synesthetic Labs Spec

## Purpose

- Deliver a working **generator → MCP validation → logged asset** pipeline.
- Show that Labs can make **schema-valid Synesthetic assets** end-to-end.
- Provide a reproducible baseline for critic, patch lifecycle, external generator integration, and RLHF extensions.

---

## Historical Scopes (≤ v0.3.3)

Versions **v0.1 → v0.3.3** covered:
- Initial generator/critic pipeline and canonical baseline assets.
- Validation over STDIO, then Unix socket, then TCP (1 MiB caps).
- Logging streams (`generator.jsonl`, `critic.jsonl`, `patches.jsonl`).
- Patch lifecycle stubs, rating stub, container hardening.
- External generator scaffolding (Gemini/OpenAI) in **mock mode**.
- Spec alignment + resolver fallback tests; `SYN_SCHEMAS_DIR` deprecated for TCP/socket.

> Full details for v0.1–v0.3.3 are **culled** from this document (refer to Git history).

---

## Scope (v0.3.4 Asset Generation Calls)

### Objectives
- Implement **live external API calls** for Gemini and OpenAI.
- Keep CI deterministic: **mock mode by default**; live mode behind env guard.
- Normalize any external output into a **schema-valid nested synesthetic asset** and **always** run MCP validation.

### Interfaces

#### ExternalGenerator (contract)
```python
class ExternalGenerator(Protocol):
    name: str                    # "gemini" | "openai"
    model: str                   # from env
    endpoint: Optional[str]      # base URL (can be None in mock mode)

    def generate(
        self,
        prompt: str,
        seed: Optional[int] = None,
        params: Optional[dict[str, Any]] = None,
        trace_id: Optional[str] = None
    ) -> dict:                   # returns normalized SynestheticAsset (nested)
        ...
```

#### CLI
```
labs generate --engine=<gemini|openai|deterministic> "prompt text"
    [--seed <int>] [--temperature <float>] [--timeout-s <int>]
    [--strict|--relaxed]  # maps to LABS_FAIL_FAST=1 or 0
```

### Environment Variables (authoritative)

| Var | Purpose | Required | Default / Notes |
|---|---|---|---|
| `MCP_ENDPOINT` | Select validator transport | No | `tcp` (primary). Accepts `tcp` \| `stdio` \| `socket`. Invalid → fallback `tcp`. |
| `MCP_HOST` | TCP host | When `MCP_ENDPOINT=tcp` | e.g., `127.0.0.1` |
| `MCP_PORT` | TCP port | When `MCP_ENDPOINT=tcp` | e.g., `7000` |
| `MCP_ADAPTER_CMD` | STDIO adapter command | When `stdio` | Adapter binary + args |
| `MCP_SOCKET_PATH` | Unix socket path | When `socket` | e.g., `/tmp/mcp.sock` |
| `LABS_FAIL_FAST` | Fail-fast toggle | No | `0` (relaxed) / `1` (strict) |
| `LABS_EXTERNAL_LIVE` | Enable live external calls | No | `0` (mocks only) |
| `GEMINI_MODEL` | Gemini model id | No | used if engine=gemini |
| `GEMINI_API_KEY` | Gemini API key | For live Gemini | — |
| `GEMINI_ENDPOINT` | Gemini API base URL | No | sensible default if unset |
| `OPENAI_MODEL` | OpenAI model id | No | used if engine=openai |
| `OPENAI_TEMPERATURE` | Default temp for OpenAI | No | CLI flag overrides |
| `OPENAI_API_KEY` | OpenAI API key | For live OpenAI | — |
| `OPENAI_ENDPOINT` | OpenAI API base URL | No | `https://api.openai.com/v1` |
| `LABS_SOCKET_TESTS` | Enable socket tests | No | `0` (skip if unsupported) |
| `SYN_SCHEMAS_DIR` | **Deprecated** (STDIO only) | No | Ignored for TCP/socket; warn once when forwarded. |

> **Transport caps:** All validator transports enforce **1 MiB** payload caps and propagate oversize failures with structured `reason`/`detail`.

### Request/Response Mapping

#### Common request envelope (before provider-specific mapping)
```json
{
  "trace_id": "<uuid4>",
  "prompt": "<user string>",
  "seed": 12345,
  "hints": {
    "need_sections": ["shader", "tone", "haptic", "controls", "meta"],
    "schema": "nested-synesthetic-asset@>=0.7.3",
    "strict_json": true
  },
  "parameters": {
    "model": "<provider model>",
    "temperature": <float|null>,
    "max_tokens": <int|null>
  }
}
```

- **Headers (live mode)**: `Authorization: Bearer <API_KEY>`, `Content-Type: application/json`.
- **Timeouts**: connect **5s**, read **30s**, total **35s** (configurable via CLI `--timeout-s`).
- **Size guards**: reject request bodies > **256 KiB**; reject raw responses > **1 MiB** pre-parse.

#### Provider specifics
- **Gemini**: POST to `${GEMINI_ENDPOINT}/…` (exact path configurable in code; default chosen to Gemini text JSON generation). Body created from the common envelope.
- **OpenAI**: POST to `${OPENAI_ENDPOINT}/chat/completions` or compatible JSON endpoint. System+user messages serialized from the common envelope.

### Normalization Contract (external → SynestheticAsset)

- **Must output** nested asset object with **sections present**:
  - `shader`: CircleSDF or provider-proposed shader; require uniforms and `input_parameters`.
  - `tone`: `Tone.Synth` baseline unless provider supplies richer but schema-valid synth.
  - `haptic`: generic device with `intensity` [0..1].
  - `controls`: at minimum `mouse.x → shader.u_px`, `mouse.y (inverted) → shader.u_py`.
  - `meta`: `title`, `description`, `category="multimodal"`, `complexity`, `tags`.
- **Fill defaults** for missing optional fields using canonical baseline.
- **Reject**: unknown keys, wrong types, missing required fields.
- **Coerce**: numeric strings → numbers where unambiguous.
- **Provenance injection** (see below) is mandatory.

### Provenance & Redaction

Provenance **must** be included under `asset.meta.provenance`:
```json
{
  "engine": "gemini|openai",
  "api_endpoint": "<base URL>",
  "api_version": "<string|unknown>",
  "model": "<model id>",
  "parameters": {"temperature": <float|null>, "seed": <int|null>},
  "trace_id": "<uuid4>",
  "mode": "mock|live",
  "timestamp": "<ISO-8601 UTC>"
}
```
- **Never** persist secrets. Redact keys in logs (`***redacted***`).
- Optionally store a short `response_hash` (SHA-256 of canonicalized raw JSON, hex, 16 chars).

### Validation (unchanged policy, explicit steps)

1. **Pre-flight**: check required sections exist; enforce numeric bounds (e.g., intensity 0..1).
2. **MCP**: invoke validator via resolved transport; **always** call even in relaxed mode.
3. **Fail-fast**:
   - Strict: any pre-flight or MCP failure → non-zero exit, log `severity=error`.
   - Relaxed: proceed to log with `severity=warning`, but **do not** persist invalid assets.

### Logging (authoritative)

- Directory: `meta/output/labs/`
  - `external.jsonl` (append-only, one JSON per line)
  - `generator.jsonl`, `critic.jsonl`, `patches.jsonl` (existing)
- **external.jsonl** entry schema (minimum):
```json
{
  "ts": "<ISO-8601 UTC>",
  "trace_id": "<uuid4>",
  "engine": "gemini|openai",
  "mode": "mock|live",
  "transport": "<tcp|stdio|socket>",
  "strict": true,
  "prompt": "<string>",
  "request": {"model": "<id>", "temperature": 0.2},
  "raw_response": {"hash": "<16-hex>", "size": 12345, "redacted": true},
  "normalized_asset": { /* nested Synesthetic asset */ },
  "mcp_result": {"ok": true, "errors": []},
  "provenance": { /* as above */ },
  "failure": null  /* or { "reason": "auth_error|timeout|bad_response|rate_limited|network_error", "detail": "<string>" } */
}
```

### Error Taxonomy & Retry

- **Reasons**:
  - `auth_error` (401/403),
  - `rate_limited` (429),
  - `timeout` (client-side expiry),
  - `network_error` (connect/reset),
  - `bad_response` (malformed JSON / schema-invalid),
  - `server_error` (5xx).
- **Retry policy** (idempotent POST):
  - `RETRY_MAX=3`, exponential backoff with jitter:
    - base **200 ms**, factor **2.0**, cap **5 s**.
  - **Do not retry** `auth_error` or `bad_response`.
- **Surface**: all terminal failures must populate `failure.reason` + `failure.detail`.

### Security

- Keys only from env; never accept via CLI args.
- Mask keys in all logs.
- Disallow file/URL fetches embedded in model outputs (no external I/O during normalization).

### Tests (authoritative matrix additions for v0.3.4)

- **Unit**
  - Endpoint resolution precedence: CLI flag > env > default.
  - Header injection: `Authorization` present only in live mode with key.
  - Size guards enforce 256 KiB request / 1 MiB response caps.
  - Retry policy honors taxonomy (no retry on auth/bad_response).
  - Normalization rejects unknown keys; fills canonical defaults.
- **Integration (mock)**
  - `labs generate --engine=gemini "prompt"` → normalized + MCP ok → persisted.
  - `labs generate --engine=openai "prompt"` → same.
  - Strict vs relaxed behavior tones (invalid asset not persisted in relaxed).
- **Error paths (mock)**
  - 401 → `auth_error`, no retry.
  - 429 → retries then `rate_limited`.
  - Timeout → retries then `timeout`.
  - Malformed JSON → `bad_response`, no retry.
- **Live (optional, skipped in CI)**
  - Gated on `LABS_EXTERNAL_LIVE=1` + provider key present.
  - Smoke: call provider, normalize, validate, persist (marked `mode=live`).
- **Validator**
  - MCP invoked in all modes (assert call count ≥1).
  - Oversize payload → structured failure bubbles to `external.jsonl`.

### Exit Criteria (v0.3.4)

- Live calls functional when `LABS_EXTERNAL_LIVE=1` and corresponding API key present.
- Normalized assets always run through MCP; invalid assets are **not** persisted.
- `external.jsonl` entries include provenance, request params, response hash, and failure (if any).
- CLI flags work; env precedence documented and tested.
- CI green with mocks; live tests optional and skipped by default.

### Docs & Ops

- Update `docs/labs_spec.md` with this v0.3.4 section.
- Update README:
  - How to set `GEMINI_API_KEY` / `OPENAI_API_KEY`.
  - Live-mode guard: `LABS_EXTERNAL_LIVE=1`.
  - Example CLI invocations.
- `.env.sample`: add new vars with empty values and comments.
- Add `docs/troubleshooting_external.md` covering error taxonomy and remedies.

### Non-Goals (v0.3.4)

- No provider-specific fine-tuning flows.
- No streaming responses; only JSON POST/parse.
- No new dependencies beyond standard HTTP client already used in repo.

---
