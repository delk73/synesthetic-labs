"""TCP transport client for MCP validation."""

from __future__ import annotations

import socket
from typing import Any, Dict

from labs.mcp.exceptions import MCPUnavailableError
from labs.transport import (
    InvalidPayloadError,
    PayloadTooLargeError,
    decode_payload,
    read_message,
    write_message,
)


class TcpMCPValidator:
    """Connect to an MCP adapter over TCP and issue validation requests."""

    def __init__(self, host: str, port: int, *, timeout: float = 10.0) -> None:
        if not host:
            raise ValueError("host must be a non-empty string")
        if port <= 0:
            raise ValueError("port must be a positive integer")
        self._host = host
        self._port = port
        self._timeout = timeout

    def validate(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Send *asset* to the MCP adapter and return the validation payload."""

        try:
            with socket.create_connection((self._host, self._port), timeout=self._timeout) as client:
                write_message(client, {"action": "validate", "asset": asset})
                response_bytes = read_message(client)
        except PayloadTooLargeError as exc:
            raise MCPUnavailableError(f"MCP request payload too large: {exc}") from exc
        except (socket.timeout, ConnectionRefusedError, ConnectionResetError, OSError) as exc:
            raise MCPUnavailableError(f"MCP TCP connection error: {exc}") from exc

        try:
            response = decode_payload(response_bytes)
        except (PayloadTooLargeError, InvalidPayloadError) as exc:
            raise MCPUnavailableError(f"Invalid MCP response: {exc}") from exc

        return response


__all__ = ["TcpMCPValidator"]
