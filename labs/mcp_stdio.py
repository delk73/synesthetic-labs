"""MCP validation bridges supporting STDIO, Unix socket, and TCP transports."""

from __future__ import annotations

import os
import shlex
import socket
import subprocess
from typing import Any, Callable, Dict, Mapping, MutableMapping, Optional, Sequence

from labs.core import normalize_resource_path
from labs.mcp.exceptions import MCPUnavailableError
from labs.transport import (
    InvalidPayloadError,
    PayloadTooLargeError,
    decode_payload,
    encode_payload,
    read_message,
    write_message,
)



class StdioMCPValidator:
    """Invoke an MCP adapter over STDIO to validate Synesthetic assets."""

    def __init__(
        self,
        command: Sequence[str],
        *,
        env: Optional[Mapping[str, str]] = None,
        timeout: float = 10.0,
    ) -> None:
        if not command:
            raise ValueError("command must include at least one argument")
        self._command: Sequence[str] = tuple(command)
        self._env = dict(env) if env is not None else None
        self._timeout = timeout

    def _combined_env(self) -> Optional[MutableMapping[str, str]]:
        if self._env is None:
            return None
        merged = os.environ.copy()
        merged.update(self._env)
        return merged

    def validate(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Send *asset* to the MCP adapter and return the validation payload."""

        try:
            request_bytes = encode_payload({"action": "validate", "asset": asset})
        except PayloadTooLargeError as exc:
            raise MCPUnavailableError(f"MCP request payload too large: {exc}") from exc

        request = request_bytes.decode("utf-8")
        try:
            process = subprocess.Popen(  # noqa: S603 - user-controlled command expected
                self._command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=self._combined_env(),
            )
        except OSError as exc:  # pragma: no cover - system-dependent failure
            raise MCPUnavailableError(f"Failed to launch MCP adapter: {exc}") from exc

        assert process.stdin is not None  # narrow type for mypy
        assert process.stdout is not None

        try:
            stdout, stderr = process.communicate(request, timeout=self._timeout)
        except subprocess.TimeoutExpired as exc:
            process.kill()
            raise MCPUnavailableError("MCP validation timed out") from exc

        if process.returncode != 0:
            message = stderr.strip() or f"exit status {process.returncode}"
            raise MCPUnavailableError(f"MCP adapter failed: {message}")

        lines = [line.strip() for line in stdout.splitlines() if line.strip()]
        if not lines:
            raise MCPUnavailableError("MCP adapter returned no output")

        response_line = lines[-1] + "\n"
        try:
            payload = decode_payload(response_line.encode("utf-8"))
        except (PayloadTooLargeError, InvalidPayloadError) as exc:
            raise MCPUnavailableError(f"Invalid MCP response: {exc}") from exc

        return payload


class SocketMCPValidator:
    """Invoke an MCP adapter over a Unix domain socket."""

    def __init__(self, path: str, *, timeout: float = 10.0) -> None:
        if not path:
            raise ValueError("path must be a non-empty string")
        self._path = path
        self._timeout = timeout

    def validate(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Send *asset* to the MCP socket server and return the validation payload."""

        try:
            payload = {"action": "validate", "asset": asset}
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.settimeout(self._timeout)
                client.connect(self._path)
                write_message(client, payload)
                response_bytes = read_message(client)
        except PayloadTooLargeError as exc:
            raise MCPUnavailableError(f"MCP request payload too large: {exc}") from exc
        except (FileNotFoundError, socket.timeout) as exc:
            raise MCPUnavailableError(f"MCP socket unavailable: {exc}") from exc
        except ConnectionError as exc:
            raise MCPUnavailableError(f"MCP socket connection error: {exc}") from exc
        except OSError as exc:
            raise MCPUnavailableError(f"MCP socket failure: {exc}") from exc

        try:
            response = decode_payload(response_bytes)
        except (PayloadTooLargeError, InvalidPayloadError) as exc:
            raise MCPUnavailableError(f"Invalid MCP response: {exc}") from exc
        return response


def build_validator_from_env(*, timeout: float = 10.0) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """Construct an MCP validator from environment configuration."""

    endpoint = os.getenv("MCP_ENDPOINT", "stdio").strip().lower()

    if endpoint in {"stdio", ""}:
        command_value = os.getenv("MCP_ADAPTER_CMD")
        if not command_value:
            raise MCPUnavailableError("MCP_ADAPTER_CMD environment variable is required")

        command = shlex.split(command_value)
        env_overrides: Dict[str, str] = {}
        schemas_dir = os.getenv("SYN_SCHEMAS_DIR")
        if schemas_dir:
            env_overrides["SYN_SCHEMAS_DIR"] = normalize_resource_path(schemas_dir)

        validator = StdioMCPValidator(command, env=env_overrides or None, timeout=timeout)
        return validator.validate

    if endpoint == "socket":
        socket_path_raw = os.getenv("MCP_SOCKET_PATH")
        socket_path = normalize_resource_path(socket_path_raw) if socket_path_raw else None
        if not socket_path:
            raise MCPUnavailableError(
                "MCP_SOCKET_PATH environment variable is required when MCP_ENDPOINT=socket"
            )

        validator = SocketMCPValidator(socket_path, timeout=timeout)
        return validator.validate

    if endpoint == "tcp":
        host = os.getenv("MCP_HOST")
        port_raw = os.getenv("MCP_PORT")
        if not host:
            raise MCPUnavailableError(
                "MCP_HOST environment variable is required when MCP_ENDPOINT=tcp"
            )
        if not port_raw:
            raise MCPUnavailableError(
                "MCP_PORT environment variable is required when MCP_ENDPOINT=tcp"
            )

        try:
            port = int(port_raw)
        except ValueError as exc:
            raise MCPUnavailableError("MCP_PORT must be an integer") from exc

        from labs.mcp.tcp_client import TcpMCPValidator

        validator = TcpMCPValidator(host.strip(), port, timeout=timeout)
        return validator.validate

    raise MCPUnavailableError(f"Unsupported MCP_ENDPOINT value: {endpoint}")


__all__ = [
    "MCPUnavailableError",
    "SocketMCPValidator",
    "StdioMCPValidator",
    "build_validator_from_env",
]
