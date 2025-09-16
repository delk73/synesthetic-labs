"""Critic agent that reviews generator proposals and coordinates MCP validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Optional, Protocol

from labs.agents.generator import GeneratorProposal
from labs.logging import LogSink, NullLogSink


class MCPAdapter(Protocol):
    """Protocol for MCP validation adapters."""

    def validate(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:  # pragma: no cover - structural
        """Validate payload and return structured MCP response."""


@dataclass(frozen=True)
class MCPValidationResult:
    """Structured representation of MCP validation output."""

    passed: bool
    details: Mapping[str, Any]


@dataclass(frozen=True)
class CritiqueResult:
    """Critic output that references the originating proposal."""

    proposal_id: str
    prompt_id: str
    notes: Iterable[str]
    recommended_action: str
    mcp: MCPValidationResult


@dataclass(frozen=True)
class CriticConfig:
    """Runtime configuration for critic evaluations."""

    minimum_required_fields: Iterable[str] = field(default_factory=lambda: ("task", "objective"))


class Critic:
    """Performs lightweight checks and defers validation to MCP adapters."""

    def __init__(
        self,
        mcp_adapter: MCPAdapter,
        log_sink: Optional[LogSink] = None,
    ) -> None:
        self._mcp = mcp_adapter
        self._log = log_sink or NullLogSink()

    def review(self, proposal: GeneratorProposal, config: Optional[CriticConfig] = None) -> CritiqueResult:
        config = config or CriticConfig()
        notes = list(self._sanity_checks(proposal, config))
        recommended_action = "ready" if not notes else "revise"
        mcp_response = self._mcp.validate(proposal.payload)
        mcp_result = MCPValidationResult(
            passed=bool(mcp_response.get("passed", False)),
            details=mcp_response,
        )
        if not mcp_result.passed and "MCP validation failed" not in notes:
            notes.append("MCP validation failed")
            recommended_action = "block"
        record = {
            "event": "critic.review",
            "proposal_id": proposal.proposal_id,
            "prompt_id": proposal.prompt_id,
            "notes": notes,
            "recommended_action": recommended_action,
            "mcp": {
                "passed": mcp_result.passed,
                "details": mcp_result.details,
            },
        }
        self._log.write(record)
        return CritiqueResult(
            proposal_id=proposal.proposal_id,
            prompt_id=proposal.prompt_id,
            notes=tuple(notes),
            recommended_action=recommended_action,
            mcp=mcp_result,
        )

    def _sanity_checks(
        self, proposal: GeneratorProposal, config: CriticConfig
    ) -> Iterable[str]:
        payload_prompt = proposal.payload.get("prompt", {})
        for field in config.minimum_required_fields:
            if field not in payload_prompt:
                yield f"Missing expected prompt field: {field}"
        if not proposal.payload.get("parameters"):
            yield "Proposal parameters are empty"

