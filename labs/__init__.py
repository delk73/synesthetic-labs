"""Synesthetic Labs package exposing core agents."""

from .agents.generator import GeneratorAgent
from .agents.critic import CriticAgent

__all__ = ["GeneratorAgent", "CriticAgent"]
