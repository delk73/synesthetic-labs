import logging

from labs import cli


def test_emit_mcp_failure_logs_transparency(caplog, monkeypatch):
    result = {
        "ok": False,
        "reason": "validation_failed",
        "schema_id": "https://schemas.synesthetic.dev/0.7.3/synesthetic-asset.schema.json",
        "schema_resolution": "inline",
        "errors": [
            {"path": "/control", "msg": "invalid type", "value": {"foo": "bar"}},
            {"path": "/haptic", "msg": 'missing property "device"'},
            {"path": "/modulations", "msg": "not an array"},
            {"path": "/extra", "msg": "should not appear"},
        ],
    }

    monkeypatch.setenv("LABS_SCHEMA_RESOLUTION", "inline")

    with caplog.at_level(logging.ERROR, logger="labs.cli"):
        cli._emit_mcp_failure_logs(result, source="confirm")

    output = "\n".join(caplog.messages)

    assert "https://schemas.synesthetic.dev/0.7.3" in output
    assert "[inline]" in output
    assert "source=confirm" in output
    assert "control" in output
    assert "invalid type" in output
    assert '{"foo": "bar"}' in output
    assert "haptic" in output
    assert 'missing property "device"' in output
    assert "modulations" in output
    assert "not an array" in output

    detail_messages = [msg for msg in caplog.messages if msg.startswith("  - ")]
    assert len(detail_messages) == 3
    assert "extra" not in output
