"""Launcher for Synesthetic Labs MCP adapters."""

from __future__ import annotations

import os
from typing import List, Optional

from labs.mcp.socket_main import main as socket_main
from labs.mcp_stub import main as stdio_main


def main(argv: Optional[List[str]] = None) -> int:
    endpoint = os.getenv("MCP_ENDPOINT", "stdio").strip().lower()
    if endpoint == "socket":
        return socket_main(argv)
    return stdio_main(argv)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
