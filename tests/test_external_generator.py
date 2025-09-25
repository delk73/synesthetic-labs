"""Tests for the ExternalGenerator integrations."""

from __future__ import annotations

import json

import pytest

from labs.generator.external import (
    ExternalGenerationError,
    GeminiGenerator,
    OpenAIGenerator,
)


def test_gemini_generator_normalises_asset(tmp_path) -> None:
    log_path = tmp_path / "external.jsonl"
    generator = GeminiGenerator(log_path=str(log_path), mock_mode=True, sleeper=lambda _: None)

    asset, context = generator.generate("ambient waves")

    assert asset["prompt"] == "ambient waves"
    provenance = asset["provenance"]["generator"]
    assert provenance["engine"] == "gemini"
    assert provenance["mode"] == "mock"
    assert provenance["api_version"] == generator.api_version
    assert asset["shader"]["component"] == "shader"
    assert asset["tone"]["component"] == "tone"

    review = {
        "ok": True,
        "validation_status": "passed",
        "mcp_response": {"status": "ok"},
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
    assert record["asset"]["provenance"]["generator"]["trace_id"] == context["trace_id"]
    assert record["review"]["validation_status"] == "passed"
    assert record["experiment_path"] == "experiments/mock.json"


def test_external_generator_logs_failure_when_transport_errors(tmp_path) -> None:
    log_path = tmp_path / "failure.jsonl"

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
    assert entry["error"].startswith("openai generation failed")
    assert len(entry["attempts"]) == 2
    assert entry["attempts"][0]["status"] == "error"
    assert "transport boom" in entry["attempts"][0]["error"]
