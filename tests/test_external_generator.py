"""Tests for the ExternalGenerator integrations."""

from __future__ import annotations

import json
import os

import pytest

from labs.generator import AssetAssembler
from labs.generator.external import (
    AzureOpenAIGenerator,
    ExternalGenerationError,
    ExternalRequestError,
    GeminiGenerator,
    MAX_RESPONSE_BYTES,
    OpenAIGenerator,
)


@pytest.fixture(autouse=True)
def _reset_fail_fast(monkeypatch) -> None:
    """Ensure LABS_FAIL_FAST defaults to strict mode during each test."""

    monkeypatch.delenv("LABS_FAIL_FAST", raising=False)


def _build_gemini_asset(
    generator: GeminiGenerator,
    prompt: str,
    schema_version: str,
) -> tuple[dict, dict, dict]:
    parameters = {"model": generator.default_model, "schema_version": schema_version}
    trace_id = "trace-1234"
    response = generator._mock_response(prompt, parameters)
    asset = generator._normalise_asset(
        response,
        prompt=prompt,
        parameters=parameters,
        response={"asset": response},
        trace_id=trace_id,
        mode="mock",
        endpoint="mock://gemini",
        response_hash="deadbeefcafefeed",
        schema_version=schema_version,
    )
    context = {
        "trace_id": trace_id,
        "prompt": prompt,
        "mode": "mock",
        "strict": True,
        "parameters": parameters,
        "request": {"model": generator.default_model},
        "request_headers": {},
        "raw_response": {
            "hash": "deadbeefcafefeed",
            "size": len(json.dumps(response)),
            "redacted": False,
        },
        "asset": asset,
        "asset_id": asset.get("asset_id"),
        "generated_at": asset.get("timestamp"),
        "schema_version": schema_version,
        "taxonomy": "external.gemini",
        "schema_binding": False,
        "schema_id": "mock-schema",
        "schema_binding_version": schema_version,
        "endpoint": "mock://gemini",
    }
    return asset, context, parameters


def test_gemini_generator_normalises_asset(tmp_path) -> None:
    log_path = tmp_path / "external.jsonl"
    generator = GeminiGenerator(log_path=str(log_path), mock_mode=True, sleeper=lambda _: None)

    asset, context, _parameters = _build_gemini_asset(generator, "ambient waves", "0.7.4")

    assert asset["prompt"] == "ambient waves"
    assert asset["provenance"]["agent"] == "ExternalGenerator"
    provenance = asset["provenance"]["generator"]
    assert provenance["engine"] == "gemini"
    assert provenance["mode"] == "mock"
    assert provenance["api_version"] == generator.api_version
    assert context["taxonomy"] == "external.gemini"
    input_parameters = asset["provenance"]["input_parameters"]
    assert input_parameters["prompt"] == "ambient waves"
    assert input_parameters["parameters"]["model"] == generator.default_model
    assert asset["control"]["control_parameters"]
    assert asset["meta_info"]["provenance"]["engine"] == "gemini"
    assert context["schema_version"] == "0.7.4"
    assert context["asset"]["$schema"] == asset["$schema"]

    review = {
        "ok": True,
        "validation_status": "passed",
        "mcp_response": {"status": "ok", "ok": True},
        "transport": "tcp",
        "strict": True,
        "mode": "strict",
        "trace_id": context["trace_id"],
    }

    generator.record_run(context=context, review=review, experiment_path="experiments/mock.json")

    entries = [
        json.loads(line)
        for line in log_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(entries) == 1
    record = entries[0]
    assert record["engine"] == "gemini"
    assert record["status"] == "validation_passed"
    assert (
        record["normalized_asset"]["meta_info"]["provenance"]["trace_id"]
        == context["trace_id"]
    )
    assert record["taxonomy"] == "external.gemini"
    assert record["raw_response"]["hash"] == context["raw_response"]["hash"]
    assert record["deployment"] == generator.default_model
    assert record["timestamp"] == record["ts"]
    assert record["raw_response"]["size"] == context["raw_response"]["size"]
    assert record["transport"] == "tcp"
    assert record["strict"] is True
    assert record["mode"] == "mock"
    assert record["experiment_path"] == "experiments/mock.json"
    assert record["schema_version"] == "0.7.4"
    assert record["$schema"] == asset["$schema"]
    assert record["failure"] is None
    assert record["schema_binding"] is False
    assert record["schema_id"] == context["schema_id"]
    assert record["endpoint"] == context["endpoint"]
    assert record["validation_status"] == "passed"
    assert isinstance(record["reviewed_at"], str)


def test_gemini_generator_legacy_schema_keeps_payload_lean() -> None:
    generator = GeminiGenerator(mock_mode=True, sleeper=lambda _: None)

    asset, context, _params = _build_gemini_asset(generator, "legacy ambient", "0.7.3")

    assert asset["$schema"].endswith("/0.7.3/synesthetic-asset.schema.json")
    assert "asset_id" not in asset
    assert "timestamp" not in asset
    assert "provenance" not in asset
    meta_info = asset.get("meta_info") or {}
    assert not meta_info.get("provenance")
    assert context["schema_version"] == "0.7.3"


def test_gemini_generate_is_placeholder() -> None:
    generator = GeminiGenerator(mock_mode=True, sleeper=lambda _: None)

    with pytest.raises(NotImplementedError) as excinfo:
        generator.generate("placeholder prompt")

    assert str(excinfo.value) == "Vertex AI structured-output unsupported"


def test_external_generator_logs_failure_when_transport_errors(monkeypatch, tmp_path) -> None:
    log_path = tmp_path / "failure.jsonl"

    monkeypatch.setenv("LABS_EXTERNAL_LIVE", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    monkeypatch.setenv("OPENAI_ENDPOINT", "https://api.openai.com/v1/chat/completions")

    def failing_transport(payload):
        raise RuntimeError("transport boom")

    generator = OpenAIGenerator(
        log_path=str(log_path),
        transport=failing_transport,
        mock_mode=False,
        max_retries=2,
        sleeper=lambda _: None,
    )

    with pytest.raises(ExternalGenerationError) as excinfo:
        generator.generate("aurora error")

    generator.record_failure(excinfo.value)

    lines = [line for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["engine"] == "openai"
    assert entry["status"] == "api_failed"
    assert len(entry["attempts"]) == 1
    attempt = entry["attempts"][0]
    assert attempt["status"] == "error"
    assert attempt["error"]["reason"] == "bad_response"
    assert "transport boom" in attempt["error"]["detail"]
    assert entry["failure"]["reason"] == "bad_response"
    assert "transport boom" in entry["failure"]["detail"]

def _minimal_asset_payload() -> dict:
    return {
        "asset": {
            "shader": {},
            "tone": {},
            "haptic": {},
            "control": {},
            "meta": {},
            "meta_info": {},
            "modulations": [],
            "rule_bundle": {},
        }
    }


def test_gemini_build_request_injects_response_mime_type() -> None:
    generator = GeminiGenerator(mock_mode=True, sleeper=lambda _: None)

    payload = generator._build_request({}, "structured", {})

    assert payload["contents"][0]["parts"][0]["text"] == "structured"
    generation_config = payload["generation_config"]
    assert generation_config["response_mime_type"] == "application/json"
    assert "tools" not in payload
    assert "tool_config" not in payload
    response_schema = generation_config.get("response_schema")
    assert isinstance(response_schema, dict)
    assert response_schema.get("$ref") == generator._latest_schema_binding["schema_id"]
    assert payload["model"] == generator.default_model


def test_gemini_build_request_merges_generation_config_parameters() -> None:
    generator = GeminiGenerator(mock_mode=True, sleeper=lambda _: None)

    payload = generator._build_request(
        {},
        "structured",
        {"temperature": 0.25, "max_tokens": 128, "seed": 42},
    )

    generation_config = payload["generation_config"]
    assert generation_config["response_mime_type"] == "application/json"
    assert generation_config["response_schema"]["$ref"] == generator._latest_schema_binding["schema_id"]
    assert generation_config["temperature"] == 0.25
    assert generation_config["max_output_tokens"] == 128
    assert generation_config["seed"] == 42
    assert payload["model"] == generator.default_model


def test_live_header_injection(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("LABS_EXTERNAL_LIVE", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "live-123")
    monkeypatch.setenv("OPENAI_ENDPOINT", "https://api.example.com/v1")

    captured: dict[str, dict[str, str]] = {}

    def fake_post_json(self, endpoint, payload, *, headers, timeout):
        captured["endpoint"] = endpoint
        captured["headers"] = dict(headers)
        response = _minimal_asset_payload()
        response["id"] = "openai-live"
        body = json.dumps(response).encode("utf-8")
        return response, body

    generator = OpenAIGenerator(
        log_path=str(tmp_path / "external.jsonl"),
        mock_mode=False,
        sleeper=lambda _: None,
    )

    monkeypatch.setattr(OpenAIGenerator, "_post_json", fake_post_json, raising=False)

    asset, context = generator.generate("live prompt", seed=7, timeout=5)
    assert not asset.get("meta_info", {}).get("provenance")
    assert captured["headers"]["Authorization"] == "Bearer live-123"
    assert context["request_headers"]["Authorization"] == "***redacted***"
    assert context["mode"] == "live"
    assert context["endpoint"] == "https://api.example.com/v1"
    assert context["schema_version"] == AssetAssembler.DEFAULT_SCHEMA_VERSION


def test_mock_mode_headers_are_empty(tmp_path) -> None:
    log_path = tmp_path / "mock.jsonl"
    generator = OpenAIGenerator(
        log_path=str(log_path),
        mock_mode=True,
        sleeper=lambda _: None,
    )

    _asset, context = generator.generate("mock prompt")
    assert context["mode"] == "mock"
    assert context["request_headers"] == {}
    assert context["endpoint"].startswith("mock://openai")
    assert context["schema_version"] == AssetAssembler.DEFAULT_SCHEMA_VERSION

    review = {
        "ok": True,
        "validation_status": "passed",
        "mcp_response": {"status": "ok", "ok": True},
        "transport": "tcp",
        "strict": True,
        "mode": "strict",
        "trace_id": context["trace_id"],
    }

    generator.record_run(context=context, review=review, experiment_path="experiments/mock.json")

    lines = [line for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["engine"] == "openai"
    assert entry["request_headers"] == {}


def test_azure_schema_binding(monkeypatch) -> None:
    monkeypatch.delenv("LABS_SCHEMA_VERSION", raising=False)
    generator = AzureOpenAIGenerator(mock_mode=True, sleeper=lambda _: None)

    _asset, context = generator.generate("schema-bound prompt")
    response_format = context["request"]["response_format"]

    assert response_format["type"] == "json_schema"
    schema_block = response_format["json_schema"]
    assert response_format["strict"] is True
    assert "strict" not in schema_block
    assert schema_block["name"].startswith("SynestheticAsset_")
    assert isinstance(schema_block["schema"], dict)
    assert context["schema_binding"] is True
    assert context["schema_id"]
    assert context["schema_binding_version"]


def test_request_body_size_cap(monkeypatch) -> None:
    monkeypatch.setenv("LABS_EXTERNAL_LIVE", "1")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "key")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://azure.example.com")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")

    generator = AzureOpenAIGenerator(mock_mode=False, sleeper=lambda _: None, max_retries=1)

    def oversized_request(self, envelope, prompt, parameters, **_):
        return {"payload": "x" * (256 * 1024 + 1)}

    monkeypatch.setattr(AzureOpenAIGenerator, "_build_request", oversized_request, raising=False)

    with pytest.raises(ExternalGenerationError) as excinfo:
        generator.generate("oversized")

    assert excinfo.value.reason == "bad_response"
    assert excinfo.value.detail == "request_body_exceeds_256KiB"
    assert excinfo.value.trace["attempts"] == []


def test_response_body_size_cap(monkeypatch) -> None:
    monkeypatch.setenv("LABS_EXTERNAL_LIVE", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    monkeypatch.setenv("OPENAI_ENDPOINT", "https://api.example.com")

    generator = OpenAIGenerator(mock_mode=False, sleeper=lambda _: None, max_retries=1)

    def huge_response(self, endpoint, payload, *, headers, timeout):
        body = b"0" * (MAX_RESPONSE_BYTES + 1)
        # The parsed payload is not read when size exceeds cap.
        return {"asset": {}}, body

    monkeypatch.setattr(OpenAIGenerator, "_post_json", huge_response, raising=False)

    with pytest.raises(ExternalGenerationError) as excinfo:
        generator.generate("oversized-response")

    assert excinfo.value.reason == "bad_response"
    assert excinfo.value.detail == "response_body_exceeds_1MiB"


def test_openai_strict_parse() -> None:
    generator = OpenAIGenerator()
    good_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({"ok": True}),
                    "role": "assistant",
                },
                "index": 0,
            }
        ]
    }
    bad_response = {
        "choices": [
            {
                "message": {
                    "content": "not-json",
                    "role": "assistant",
                },
                "index": 0,
            }
        ]
    }

    assert generator._extract_structured_payload(good_response)["ok"] is True
    with pytest.raises(ExternalRequestError) as excinfo:
        generator._extract_structured_payload(bad_response)
    assert excinfo.value.reason == "bad_response"


def test_no_retry_on_auth_error(monkeypatch) -> None:
    monkeypatch.setenv("LABS_EXTERNAL_LIVE", "1")
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://azure.example.com")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")

    generator = AzureOpenAIGenerator(mock_mode=False, sleeper=lambda _: None, max_retries=3)

    with pytest.raises(ExternalGenerationError) as excinfo:
        generator.generate("auth fail")

    trace = excinfo.value.trace
    assert excinfo.value.reason == "auth_error"
    assert len(trace["attempts"]) == 1
    assert trace["attempts"][0]["error"]["reason"] == "auth_error"


def test_rate_limited_retries(monkeypatch) -> None:
    monkeypatch.setenv("LABS_EXTERNAL_LIVE", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    monkeypatch.setenv("OPENAI_ENDPOINT", "https://api.example.com")

    generator = OpenAIGenerator(mock_mode=False, sleeper=lambda _: None, max_retries=3)

    call_count = {"n": 0}

    def flaky_post_json(self, endpoint, payload, *, headers, timeout):
        call_count["n"] += 1
        if call_count["n"] < 3:
            raise ExternalRequestError("rate_limited", "status_429", retryable=True)
        response = _minimal_asset_payload()
        response["id"] = "final"
        body = json.dumps(response).encode("utf-8")
        return response, body

    monkeypatch.setattr(OpenAIGenerator, "_post_json", flaky_post_json, raising=False)

    asset, context = generator.generate("rate limited", schema_version="0.7.4")

    assert call_count["n"] == 3
    assert asset["asset_id"]
    assert context["schema_version"] == "0.7.4"
    assert len(context["attempts"]) == 3
    assert context["attempts"][0]["status"] == "error"
    assert context["attempts"][-1]["status"] == "ok"


def test_normalization_populates_defaults() -> None:
    generator = GeminiGenerator(mock_mode=True, sleeper=lambda _: None)
    response = {
        "id": "mock",
        "asset": {
            "shader": {},
            "tone": {},
            "haptic": {},
            "control": {},
            "meta": {},
            "meta_info": {},
            "modulations": [],
            "rule_bundle": {},
        },
    }
    asset = generator._normalise_asset(
        response["asset"],
        prompt="prompt",
        parameters={"model": "gemini-pro"},
        response=response,
        trace_id="trace",
        mode="mock",
        endpoint="https://example.com",
        response_hash="abc123def4567890",
        schema_version="0.7.4",
    )
    assert asset["meta_info"]["provenance"]["engine"] == "gemini"
    control_pairs = {
        tuple((combo.get("device"), combo.get("control")))
        for parameter in asset["control"]["control_parameters"]
        for combo in parameter.get("combo", [])
        if isinstance(combo, dict)
    }
    assert ("mouse", "x") in control_pairs
    assert ("mouse", "y") in control_pairs


def test_normalization_rejects_unknown_keys() -> None:
    generator = GeminiGenerator(mock_mode=True, sleeper=lambda _: None)
    payload = {
        "shader": {},
        "tone": {},
        "haptic": {},
        "control": {},
        "meta": {},
        "meta_info": {},
        "modulations": [],
        "rule_bundle": {},
        "unexpected": {},
    }
    with pytest.raises(ExternalRequestError) as excinfo:
            generator._normalise_asset(
                payload,
                prompt="prompt",
                parameters={},
                response={"asset": payload},
                trace_id="trace",
                mode="mock",
                endpoint="mock://gemini",
                response_hash="abc1230000000000",
                schema_version="0.7.4",
            )
    assert excinfo.value.reason == "bad_response"
    assert excinfo.value.detail.startswith("unknown_key")


def test_normalization_rejects_out_of_range_values() -> None:
    generator = GeminiGenerator(mock_mode=True, sleeper=lambda _: None)
    payload = {
        "shader": {
            "input_parameters": [
                {
                    "parameter": "shader.u_px",
                    "minimum": -1.0,
                    "maximum": 1.0,
                    "default": 5.0,
                }
            ]
        },
        "tone": {},
        "haptic": {
            "profile": {"intensity": 2.0}
        },
        "control": {},
        "meta": {},
        "meta_info": {},
        "modulations": [],
        "rule_bundle": {},
    }
    with pytest.raises(ExternalRequestError) as excinfo:
            generator._normalise_asset(
                payload,
                prompt="prompt",
                parameters={},
                response={"asset": payload},
                trace_id="trace",
                mode="mock",
                endpoint="mock://gemini",
                response_hash="abc1230000000000",
                schema_version="0.7.4",
            )
    assert excinfo.value.reason == "bad_response"
    assert "out_of_range" in excinfo.value.detail or "invalid_bounds" in excinfo.value.detail


def test_normalization_merges_existing_provenance_input_parameters() -> None:
    generator = GeminiGenerator(mock_mode=True, sleeper=lambda _: None)
    response = {
        "id": "existing-response",
        "asset": {
            "shader": {},
            "tone": {},
            "haptic": {},
            "control": {},
            "meta": {},
            "meta_info": {},
            "modulations": [],
            "rule_bundle": {},
            "provenance": {
                "input_parameters": {
                    "prompt": "seed prompt",
                    "parameters": {"alpha": 1},
                    "notes": ["preserve"],
                },
                "generator": {"response_id": "existing-response"},
            },
        },
    }

    asset = generator._normalise_asset(
        response["asset"],
        prompt="merged prompt",
        parameters={"model": "gemini-pro", "seed": 5},
        response=response,
        trace_id="trace",
        mode="mock",
        endpoint="mock://gemini",
        response_hash="abc123def456",
        schema_version="0.7.4",
    )

    provenance = asset["provenance"]
    input_parameters = provenance["input_parameters"]
    assert input_parameters["prompt"] == "merged prompt"
    assert input_parameters["notes"] == ["preserve"]
    assert input_parameters["parameters"]["alpha"] == 1
    assert input_parameters["parameters"]["seed"] == 5
    assert provenance["generator"]["response_id"] == "existing-response"
