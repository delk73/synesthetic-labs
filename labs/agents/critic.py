"""Critic agent validates generator proposals before MCP handoff."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from labs.logging import log_jsonl

Proposal = Dict[str, Any]
ValidationResult = Dict[str, Any]
ReviewPackage = Dict[str, Any]


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


Validator = Callable[[Proposal], ValidationResult]


@dataclass
class CriticAgent:
    """Review generator proposals and coordinate MCP validation."""

    output_path: Path | str = Path("meta/output/critic.log.jsonl")
    mcp_validator: Optional[Validator] = None
    clock: Callable[[], datetime] = field(default_factory=_default_clock)

    def __post_init__(self) -> None:
        self.output_path = Path(self.output_path)
        self.logger = logging.getLogger(self.__class__.__name__)

    def review(self, proposal: Proposal) -> ReviewPackage:
        """Return a review payload containing critique and validation info."""
        if not isinstance(proposal, dict):
            raise TypeError("Proposal must be a dictionary")

        reviewed_at = self.clock().replace(microsecond=0, tzinfo=timezone.utc)
        issues: List[str] = self._collect_issues(proposal)
        validation = self._validate(proposal, issues)
        ok = not issues and bool(validation.get("passed"))
        critique = {
            "proposal_id": proposal.get("proposal_id"),
            "reviewed_at": reviewed_at.isoformat(),
            "issues": issues,
            "recommendations": self._build_recommendations(issues),
        }

        package: ReviewPackage = {
            "proposal": proposal,
            "critique": critique,
            "validation": validation,
            "ok": ok,
        }

        log_jsonl(self.output_path, {"event": "critic.review", "result": package})
        self.logger.debug("Review for proposal %s complete; ok=%s", proposal.get("proposal_id"), ok)
        return package

    # Internal helpers ---------------------------------------------------
    def _collect_issues(self, proposal: Proposal) -> List[str]:
        issues: List[str] = []
        required_fields = ["proposal_id", "prompt_id", "prompt", "asset", "generated_at"]
        for field in required_fields:
            if field not in proposal:
                issues.append(f"missing field: {field}")

        asset = proposal.get("asset")
        if not isinstance(asset, dict):
            issues.append("asset payload must be a dictionary")
        else:
            if not asset.get("description"):
                issues.append("asset description is empty")
            if not asset.get("type"):
                issues.append("asset type is missing")
        return issues

    def _validate(self, proposal: Proposal, issues: List[str]) -> ValidationResult:
        if self.mcp_validator is None:
            message = "MCP validator not configured; validation skipped"
            issues.append(message)
            return {"passed": False, "status": "skipped", "reason": message}

        try:
            validation = self.mcp_validator(proposal)
        except Exception as exc:  # pragma: no cover - defensive guard
            message = f"validator error: {exc}"
            issues.append(message)
            return {"passed": False, "status": "error", "reason": message}

        if "passed" not in validation:
            issues.append("validator response missing 'passed' flag")
            return {**validation, "passed": False, "status": "invalid"}

        if not validation.get("passed") and "reason" not in validation:
            validation = {**validation, "reason": "validator reported failure"}
        return validation

    def _build_recommendations(self, issues: List[str]) -> List[str]:
        if not issues:
            return ["ready for MCP submission"]
        return [f"address: {issue}" for issue in issues]
