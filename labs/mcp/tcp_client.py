"""TCP transport client for MCP validation."""

from __future__ import annotations

import socket
import uuid
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
                write_message(client, _jsonrpc_request(asset))
                response_bytes = read_message(client)
        except PayloadTooLargeError as exc:
            raise MCPUnavailableError(f"MCP request payload too large: {exc}") from exc
        except (socket.timeout, ConnectionRefusedError, ConnectionResetError, OSError) as exc:
            raise MCPUnavailableError(f"MCP TCP connection error: {exc}") from exc

        try:
            response = decode_payload(response_bytes)
        except (PayloadTooLargeError, InvalidPayloadError) as exc:
            raise MCPUnavailableError(f"Invalid MCP response: {exc}") from exc

        if not isinstance(response, dict):
            raise MCPUnavailableError("Invalid MCP response payload")

        return _unwrap_jsonrpc(response)


def _jsonrpc_request(asset: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "validate",
        "params": {"asset": asset},
    }


def _unwrap_jsonrpc(payload: Dict[str, Any]) -> Dict[str, Any]:
    if payload.get("jsonrpc") == "2.0":
        if "error" in payload:
            error = payload["error"]
            message = error.get("message") if isinstance(error, dict) else str(error)
            raise MCPUnavailableError(f"MCP error response: {message}")
        result = payload.get("result")
        if isinstance(result, dict):
            return result
        raise MCPUnavailableError("MCP response missing result payload")
    return payload


def get_schema_from_mcp(
    schema_name: str, 
    *, 
    version: str | None = None,
    host: str | None = None, 
    port: int | None = None,
    timeout: float = 10.0
) -> Dict[str, Any]:
    """Call the MCP server's get_schema tool via TCP.
    
    Args:
        schema_name: Name of the schema (e.g., "synesthetic-asset")
        version: Optional version string (e.g., "0.7.3")
        host: MCP server host (defaults to MCP_HOST env or "127.0.0.1")
        port: MCP server port (defaults to MCP_PORT env or 8765)
        timeout: Connection timeout in seconds
        
    Returns:
        MCP response payload with schema
        
    Raises:
        MCPUnavailableError: If connection fails or response is invalid
    """
    import os
    
    if host is None:
        host = os.getenv("MCP_HOST", "127.0.0.1")
    if port is None:
        port = int(os.getenv("MCP_PORT", "8765"))
        
    params: Dict[str, Any] = {"name": schema_name}
    if version is not None:
        params["version"] = version
    
    # MCP server expects direct method calls, not tools/call wrapper
    request = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "get_schema",
        "params": params
    }
    
    try:
        with socket.create_connection((host, port), timeout=timeout) as client:
            write_message(client, request)
            response_bytes = read_message(client)
    except PayloadTooLargeError as exc:
        raise MCPUnavailableError(f"MCP request payload too large: {exc}") from exc
    except (socket.timeout, ConnectionRefusedError, ConnectionResetError, OSError) as exc:
        raise MCPUnavailableError(f"MCP TCP connection error: {exc}") from exc
    
    try:
        response = decode_payload(response_bytes)
    except (PayloadTooLargeError, InvalidPayloadError) as exc:
        raise MCPUnavailableError(f"Invalid MCP response: {exc}") from exc
    
    if not isinstance(response, dict):
        raise MCPUnavailableError("Invalid MCP response payload")
    
    return _unwrap_jsonrpc(response)


__all__ = ["TcpMCPValidator", "get_schema_from_mcp"]
