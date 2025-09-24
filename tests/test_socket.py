"""Tests for the Unix socket MCP adapter."""

from __future__ import annotations

import socket
import threading
from typing import List

import pytest

from labs.mcp import socket_main
from labs.transport import MAX_PAYLOAD_BYTES, PayloadTooLargeError, decode_payload, read_message, write_message


def _connect_or_skip(client: socket.socket, path: str) -> None:
    try:
        client.connect(path)
    except PermissionError:
        pytest.skip("Unix domain sockets are not permitted in this sandbox")


def _run_server(path: str, errors: List[BaseException]) -> None:
    try:
        socket_main.serve_once(path)
    except Exception as exc:  # pragma: no cover - test harness captures failures
        errors.append(exc)


def test_socket_round_trip(tmp_path) -> None:
    path = tmp_path / "mcp.sock"
    errors: List[BaseException] = []
    server = threading.Thread(target=_run_server, args=(str(path), errors), daemon=True)
    server.start()

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        _connect_or_skip(client, str(path))
        write_message(client, {"action": "validate", "asset": {"id": "sock-1"}})
        response_bytes = read_message(client)

    server.join(timeout=1.0)
    assert not server.is_alive()
    assert not errors
    assert not path.exists()

    response = decode_payload(response_bytes)
    assert response["status"] == "ok"
    assert response["asset_id"] == "sock-1"


def test_socket_payload_cap(tmp_path) -> None:
    path = tmp_path / "mcp.sock"
    errors: List[BaseException] = []
    server = threading.Thread(target=_run_server, args=(str(path), errors), daemon=True)
    server.start()

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        _connect_or_skip(client, str(path))
        oversize = b"{" + b"a" * (MAX_PAYLOAD_BYTES + 1) + b"}\n"
        client.sendall(oversize)
        client.shutdown(socket.SHUT_WR)
        # Server should close the connection after detecting the oversize payload.
        with pytest.raises((ConnectionResetError, BrokenPipeError, ConnectionAbortedError, OSError)):
            client.recv(1)

    server.join(timeout=1.0)
    assert not server.is_alive()
    assert errors
    assert isinstance(errors[0], PayloadTooLargeError)
    assert not path.exists()


def test_socket_unlinks_existing_file(tmp_path) -> None:
    path = tmp_path / "mcp.sock"
    path.write_text("placeholder", encoding="utf-8")

    errors: List[BaseException] = []
    server = threading.Thread(target=_run_server, args=(str(path), errors), daemon=True)
    server.start()

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        _connect_or_skip(client, str(path))
        write_message(client, {"action": "validate", "asset": {"id": "sock-2"}})
        _ = read_message(client)

    server.join(timeout=1.0)
    assert not server.is_alive()
    assert not errors
    assert not path.exists()
