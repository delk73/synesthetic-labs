"""Synesthetic Labs package exposing generator and critic agents."""

from .agents.generator import GeneratorAgent
from .agents.critic import CriticAgent

__all__ = ["GeneratorAgent", "CriticAgent"]
