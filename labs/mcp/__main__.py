"""Placeholder CLI for MCP adapters.

TCP is the only supported transport; use :mod:`labs.mcp_stdio` helpers directly.
"""

from __future__ import annotations

def main(argv=None) -> int:
    raise SystemExit("MCP CLI entrypoint is deprecated; use TCP via labs.mcp_stdio.")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
