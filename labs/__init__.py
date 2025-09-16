"""Entry points for the Synesthetic Labs package."""

from .agents.generator import Generator, GeneratorConfig, GeneratorProposal
from .agents.critic import Critic, CriticConfig, CritiqueResult, MCPValidationResult

__all__ = [
    "Generator",
    "GeneratorConfig",
    "GeneratorProposal",
    "Critic",
    "CriticConfig",
    "CritiqueResult",
    "MCPValidationResult",
]
