"""Command line entry point for Synesthetic Labs."""

from __future__ import annotations

import argparse
import json
import logging
import os
import socket
import sys
from typing import Any, Dict, Optional

from labs.agents.generator import GeneratorAgent
from labs.agents.critic import CriticAgent, MCPUnavailableError

_LOGGER = logging.getLogger("labs.cli")


class SocketMCPValidator:
    """Minimal TCP validator client for MCP adapters.

    The implementation is intentionally lightweight: it opens a TCP connection
    to the configured host/port, sends a JSON payload, and expects a JSON
    response. Failures are surfaced as :class:`MCPUnavailableError` so the
    critic can fall back gracefully.
    """

    def __init__(self, host: str, port: int, *, timeout: float = 1.0) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout

    def validate(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        message = json.dumps({"action": "validate", "asset": asset}).encode("utf-8")
        try:
            with socket.create_connection((self.host, self.port), timeout=self.timeout) as conn:
                conn.sendall(message)
                conn.shutdown(socket.SHUT_WR)
                payload = conn.recv(65536)
        except OSError as exc:
            raise MCPUnavailableError(str(exc)) from exc

        if not payload:
            raise MCPUnavailableError("no response from MCP adapter")

        try:
            return json.loads(payload.decode("utf-8"))
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive fallback
            raise MCPUnavailableError(f"invalid MCP response: {exc}") from exc


def _configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def _load_asset(value: str) -> Dict[str, Any]:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        with open(value, "r", encoding="utf-8") as handle:
            return json.load(handle)


def _build_validator() -> Optional[Any]:
    host = os.getenv("MCP_HOST")
    port_value = os.getenv("MCP_PORT")
    if not host or not port_value:
        _LOGGER.info("MCP validation skipped: MCP_HOST/MCP_PORT not configured")
        return None

    try:
        port = int(port_value)
    except ValueError:
        _LOGGER.warning("MCP validation skipped: invalid MCP_PORT %s", port_value)
        return None

    schemas_dir = os.getenv("SYN_SCHEMAS_DIR")
    if not schemas_dir:
        _LOGGER.info("MCP validation skipped: SYN_SCHEMAS_DIR not configured")
        return None

    validator = SocketMCPValidator(host, port)
    _LOGGER.debug("Configured MCP validator for %s:%s", host, port)
    return validator.validate


def main(argv: Optional[list[str]] = None) -> int:
    """Entry point for the Labs CLI."""

    _configure_logging()

    parser = argparse.ArgumentParser(description="Synesthetic Labs CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate", help="Generate a proposal from a prompt")
    generate_parser.add_argument("prompt", help="Prompt text for the generator")

    critique_parser = subparsers.add_parser("critique", help="Critique a proposal JSON payload")
    critique_parser.add_argument("asset", help="JSON string or file path pointing to the asset")

    args = parser.parse_args(argv)

    if args.command == "generate":
        agent = GeneratorAgent()
        proposal = agent.propose(args.prompt)
        print(json.dumps(proposal, indent=2))
        return 0

    if args.command == "critique":
        asset = _load_asset(args.asset)
        validator_callback = _build_validator()
        critic = CriticAgent(validator=validator_callback)
        review = critic.review(asset)
        print(json.dumps(review, indent=2))
        return 0

    parser.error("Unknown command")
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
