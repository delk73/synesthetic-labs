"""STDIO-based MCP validation bridge."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
from typing import Any, Callable, Dict, Mapping, MutableMapping, Optional, Sequence


class MCPUnavailableError(RuntimeError):
    """Raised when the MCP validator cannot be reached."""


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

        request = json.dumps({"action": "validate", "asset": asset}) + "\n"
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

        response_text = lines[-1]
        try:
            payload = json.loads(response_text)
        except json.JSONDecodeError as exc:
            snippet = response_text[:200]
            raise MCPUnavailableError(f"Invalid MCP response: {exc}: {snippet}") from exc

        if not isinstance(payload, dict):
            raise MCPUnavailableError("MCP response was not a JSON object")
        return payload


def build_validator_from_env(*, timeout: float = 10.0) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """Construct a STDIO MCP validator from environment configuration."""

    command_value = os.getenv("MCP_ADAPTER_CMD")
    if not command_value:
        raise MCPUnavailableError("MCP_ADAPTER_CMD environment variable is required")

    command = shlex.split(command_value)
    env_overrides: Dict[str, str] = {}
    schemas_dir = os.getenv("SYN_SCHEMAS_DIR")
    if schemas_dir:
        env_overrides["SYN_SCHEMAS_DIR"] = schemas_dir

    validator = StdioMCPValidator(command, env=env_overrides or None, timeout=timeout)
    return validator.validate


__all__ = [
    "MCPUnavailableError",
    "StdioMCPValidator",
    "build_validator_from_env",
]
