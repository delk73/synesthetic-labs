"""Agent interfaces for Synesthetic Labs."""

from .generator import Generator, GeneratorConfig, GeneratorProposal
from .critic import Critic, CriticConfig, CritiqueResult, MCPValidationResult

__all__ = [
    "Generator",
    "GeneratorConfig",
    "GeneratorProposal",
    "Critic",
    "CriticConfig",
    "CritiqueResult",
    "MCPValidationResult",
]
