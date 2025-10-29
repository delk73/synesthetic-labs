"""TCP-only MCP validation helpers."""

from __future__ import annotations

import os
from typing import Callable, Dict

from labs.mcp.exceptions import MCPUnavailableError
from labs.mcp.tcp_client import TcpMCPValidator


def resolve_mcp_endpoint() -> str:
    """Return the effective MCP transport. Always ``tcp``."""

    return "tcp"


def build_validator_from_env(*, timeout: float = 10.0) -> Callable[[Dict[str, object]], Dict[str, object]]:
    """Construct a TCP MCP validator using environment configuration.

    Raises:
        MCPUnavailableError: If host or port configuration is missing or invalid.
    """

    host = os.getenv("MCP_HOST", "127.0.0.1").strip()
    port_raw = os.getenv("MCP_PORT", "8765").strip()
    if not host:
        raise MCPUnavailableError("MCP_HOST is required for TCP transport")
    try:
        port = int(port_raw)
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise MCPUnavailableError("MCP_PORT must be an integer") from exc

    validator = TcpMCPValidator(host, port, timeout=timeout)
    return validator.validate


__all__ = ["build_validator_from_env", "resolve_mcp_endpoint"]
