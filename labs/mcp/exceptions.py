"""Shared MCP transport exceptions."""

from __future__ import annotations


class MCPUnavailableError(RuntimeError):
    """Raised when the MCP validator cannot be reached."""


__all__ = ["MCPUnavailableError"]
