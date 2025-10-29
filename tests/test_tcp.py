"""Tests for the TCP MCP validator."""

from __future__ import annotations

import socket
import threading
from typing import Dict, List

import pytest

from labs.mcp.exceptions import MCPUnavailableError
from labs.mcp.tcp_client import TcpMCPValidator
from labs.mcp_stdio import build_validator_from_env, resolve_mcp_endpoint
from labs.transport import MAX_PAYLOAD_BYTES, decode_payload, read_message, write_message

pytestmark = pytest.mark.requires_real_tcp


def _start_tcp_server(handler) -> tuple[threading.Thread, int, List[BaseException]]:
    ready = threading.Event()
    errors: List[BaseException] = []
    port_holder: Dict[str, int] = {}

    def run() -> None:
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except PermissionError as exc:  # pragma: no cover - sandbox restriction
            port_holder["error"] = exc
            ready.set()
            return

        with server:
            try:
                server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server.bind(("127.0.0.1", 0))
                server.listen(1)
            except PermissionError as exc:  # pragma: no cover - sandbox restriction
                port_holder["error"] = exc
                ready.set()
                return

            port_holder["port"] = server.getsockname()[1]
            ready.set()
            try:
                conn, _ = server.accept()
            except Exception as exc:  # pragma: no cover - defensive
                errors.append(exc)
                return
            with conn:
                try:
                    raw = read_message(conn)
                    response = handler(raw)
                    write_message(conn, response)
                except Exception as exc:  # pragma: no cover - surfaced in assertions
                    errors.append(exc)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    if not ready.wait(timeout=2.0):  # pragma: no cover - defensive
        raise RuntimeError("Server failed to start")

    if "error" in port_holder:
        thread.join(timeout=1.0)
        raise port_holder["error"]
    return thread, port_holder["port"], errors


def test_tcp_round_trip() -> None:
    def handler(raw: bytes) -> Dict[str, object]:
        request = decode_payload(raw)
        assert request["jsonrpc"] == "2.0"
        asset = request["params"]["asset"]
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {"status": "ok", "asset_id": asset.get("asset_id")},
        }

    try:
        thread, port, errors = _start_tcp_server(handler)
    except PermissionError:
        pytest.skip("TCP sockets are not permitted in this sandbox")

    validator = TcpMCPValidator("127.0.0.1", port)
    response = validator.validate({"asset_id": "tcp-1"})

    thread.join(timeout=1.0)
    assert not thread.is_alive()
    assert not errors
    assert response == {"status": "ok", "asset_id": "tcp-1"}


def test_build_validator_from_env_tcp(monkeypatch) -> None:
    def handler(raw: bytes) -> Dict[str, object]:
        request = decode_payload(raw)
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {"status": "ok", "endpoint": request["params"]["asset"].get("asset_id")},
        }

    try:
        thread, port, errors = _start_tcp_server(handler)
    except PermissionError:
        pytest.skip("TCP sockets are not permitted in this sandbox")

    monkeypatch.setenv("MCP_ENDPOINT", "tcp")
    monkeypatch.setenv("MCP_HOST", "127.0.0.1")
    monkeypatch.setenv("MCP_PORT", str(port))

    validator = build_validator_from_env(timeout=2.0)
    response = validator({"asset_id": "tcp-env"})

    thread.join(timeout=1.0)
    assert not thread.is_alive()
    assert not errors
    assert response == {"status": "ok", "endpoint": "tcp-env"}


def test_tcp_payload_cap() -> None:
    def handler(_: bytes) -> Dict[str, object]:  # pragma: no cover - not expected to run
        return {"jsonrpc": "2.0", "id": "1", "result": {"status": "unexpected"}}

    try:
        thread, port, errors = _start_tcp_server(handler)
    except PermissionError:
        pytest.skip("TCP sockets are not permitted in this sandbox")

    validator = TcpMCPValidator("127.0.0.1", port)
    oversize = "x" * (MAX_PAYLOAD_BYTES + 10)

    with pytest.raises(MCPUnavailableError) as excinfo:
        validator.validate({"asset_id": "large", "data": oversize})

    assert "too large" in str(excinfo.value)

    thread.join(timeout=1.0)
    assert not thread.is_alive()
    # Connection closes without completing a payload; we expect the server to record a ConnectionError.
    assert errors and any(isinstance(err, ConnectionError) for err in errors)


def test_tcp_connection_error() -> None:
    validator = TcpMCPValidator("127.0.0.1", 65530)
    with pytest.raises(MCPUnavailableError) as excinfo:
        validator.validate({"asset_id": "missing"})
    assert "connection error" in str(excinfo.value).lower()


def test_build_validator_from_env_defaults_to_tcp(monkeypatch) -> None:
    def handler(raw: bytes) -> Dict[str, object]:
        request = decode_payload(raw)
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {"status": "ok", "endpoint": request["params"]["asset"].get("asset_id")},
        }

    try:
        thread, port, errors = _start_tcp_server(handler)
    except PermissionError:
        pytest.skip("TCP sockets are not permitted in this sandbox")

    monkeypatch.delenv("MCP_ENDPOINT", raising=False)
    monkeypatch.setenv("MCP_HOST", "127.0.0.1")
    monkeypatch.setenv("MCP_PORT", str(port))

    validator = build_validator_from_env(timeout=2.0)
    response = validator({"asset_id": "tcp-default"})

    thread.join(timeout=1.0)
    assert not thread.is_alive()
    assert not errors
    assert response == {"status": "ok", "endpoint": "tcp-default"}


def test_resolve_mcp_endpoint_unset_defaults_to_tcp(monkeypatch) -> None:
    monkeypatch.delenv("MCP_ENDPOINT", raising=False)

    endpoint = resolve_mcp_endpoint()

    assert endpoint == "tcp"


def test_resolve_mcp_endpoint_invalid_defaults_to_tcp(monkeypatch) -> None:
    monkeypatch.setenv("MCP_ENDPOINT", "bogus")

    endpoint = resolve_mcp_endpoint()

    assert endpoint == "tcp"
