"""Common transport helpers for MCP communication."""

from __future__ import annotations

import json
from typing import Any, Dict, Mapping

MAX_PAYLOAD_BYTES = 1024 * 1024
_DELIMITER = b"\n"


class PayloadTooLargeError(RuntimeError):
    """Raised when a transport payload exceeds the configured size limit."""


class InvalidPayloadError(RuntimeError):
    """Raised when a transport payload cannot be decoded as JSON."""


def _ensure_under_limit(data: bytes) -> None:
    if len(data) > MAX_PAYLOAD_BYTES:
        raise PayloadTooLargeError(
            f"payload size {len(data)} bytes exceeds cap of {MAX_PAYLOAD_BYTES} bytes"
        )


def encode_payload(payload: Mapping[str, Any]) -> bytes:
    """Serialize *payload* to JSON bytes enforcing the global size cap."""

    text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    data = text.encode("utf-8")
    _ensure_under_limit(data)
    return data + _DELIMITER


def decode_payload(data: bytes) -> Dict[str, Any]:
    """Decode transport *data* into a JSON object enforcing the size cap."""

    if data.endswith(_DELIMITER):
        data = data[:-1]
    _ensure_under_limit(data)
    try:
        loaded = json.loads(data.decode("utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive guard
        snippet = data[:200].decode("utf-8", errors="replace")
        raise InvalidPayloadError(f"invalid JSON payload: {exc}: {snippet}") from exc

    if not isinstance(loaded, dict):
        raise InvalidPayloadError("transport payload must decode to a JSON object")
    return loaded


def read_message(sock) -> bytes:
    """Read a newline-delimited message from *sock* enforcing the size cap."""

    chunks = bytearray()
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            raise ConnectionError("socket closed before newline-delimited payload was received")
        chunks.extend(chunk)
        if len(chunks) > MAX_PAYLOAD_BYTES + len(_DELIMITER):
            raise PayloadTooLargeError(
                f"payload size {len(chunks)} bytes exceeds cap of {MAX_PAYLOAD_BYTES} bytes"
            )
        if chunks.endswith(_DELIMITER):
            break
    return bytes(chunks)


def write_message(sock, payload: Mapping[str, Any]) -> None:
    """Send *payload* over *sock* using the newline-delimited framing."""

    data = encode_payload(payload)
    totalsent = 0
    while totalsent < len(data):
        sent = sock.send(data[totalsent:])
        if sent == 0:
            raise ConnectionError("socket connection broken during send")
        totalsent += sent


__all__ = [
    "MAX_PAYLOAD_BYTES",
    "InvalidPayloadError",
    "PayloadTooLargeError",
    "decode_payload",
    "encode_payload",
    "read_message",
    "write_message",
]
