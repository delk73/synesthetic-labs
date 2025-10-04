"""Unix socket MCP adapter entrypoint."""

from __future__ import annotations

import argparse
import os
import socket
from typing import Any, Callable, Dict

from labs.mcp_stub import _success_response
from labs.transport import PayloadTooLargeError, decode_payload, read_message, write_message


def _default_handler(request: Dict[str, Any]) -> Dict[str, Any]:
    """Return the canonical MCP stub response."""

    return _success_response(request)


def serve_once(path: str, handler: Callable[[Dict[str, Any]], Dict[str, Any]] | None = None) -> None:
    """Serve a single MCP request over *path* and unlink the socket when done."""

    if not path:
        raise ValueError("path must be a non-empty string")

    if os.path.exists(path):
        os.unlink(path)

    handler = handler or _default_handler

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        server.bind(path)
        server.listen(1)

        conn, _ = server.accept()
        with conn:
            raw = read_message(conn)
            request = decode_payload(raw)
            response = handler(request)
            write_message(conn, response)
    finally:
        server.close()
        if os.path.exists(path):
            os.unlink(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Synesthetic Labs MCP socket adapter")
    parser.add_argument("--path", help="Unix domain socket path; defaults to MCP_SOCKET_PATH")
    args = parser.parse_args(argv)

    path = args.path or os.getenv("MCP_SOCKET_PATH")
    if not path:
        parser.error("socket path must be provided via --path or MCP_SOCKET_PATH")

    try:
        serve_once(path)
    except PayloadTooLargeError as exc:
        print(f"payload too large: {exc}", file=os.sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - defensive guard
        print(f"socket adapter failed: {exc}", file=os.sys.stderr)
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
