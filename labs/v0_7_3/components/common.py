"""Shared helper utilities for component builders."""

from __future__ import annotations

import math
import re
from typing import Iterable, List, Sequence

from labs.v0_7_3.prompt_parser import PromptSemantics, parse_prompt

_NAME_SANITISER = re.compile(r"[^a-z0-9_]+")

_INTENSITY_TO_SCALAR = {
    "gentle": 0.4,
    "warm": 0.55,
    "soft": 0.45,
    "mellow": 0.5,
    "bright": 0.65,
    "vibrant": 0.7,
    "energetic": 0.8,
    "intense": 0.9,
    "sharp": 0.85,
}


def ensure_semantics(prompt: str, semantics: PromptSemantics | None) -> PromptSemantics:
    """Return *semantics*, parsing *prompt* if necessary."""
    return semantics or parse_prompt(prompt)


def sanitize_identifier(text: str, fallback: str, *, max_length: int = 60) -> str:
    """Return lowercase identifier derived from *text*."""
    candidate = text.strip().lower().replace(" ", "_")
    candidate = _NAME_SANITISER.sub("_", candidate)
    candidate = candidate.strip("_") or fallback
    return candidate[:max_length]


def intensity_scalar(semantics: PromptSemantics, *, default: float = 0.7) -> float:
    """Map semantic intensity to scalar multiplier."""
    if semantics.intensity:
        return _INTENSITY_TO_SCALAR.get(semantics.intensity, default)
    if semantics.mood == "ambient":
        return 0.5
    return default


def tempo_from_semantics(
    semantics: PromptSemantics,
    *,
    default: float = 60.0,
    clamp: Sequence[float] | None = (30.0, 180.0),
) -> float:
    """Return tempo (BPM) inferred from semantics."""
    tempo = semantics.tempo_bpm or default
    if clamp:
        low, high = clamp
        tempo = max(low, min(high, tempo))
    return tempo


def frequency_from_semantics(
    semantics: PromptSemantics,
    *,
    default: float = 440.0,
    clamp: Sequence[float] | None = (40.0, 12000.0),
) -> float:
    """Return frequency (Hz) inferred from semantics."""
    freq = semantics.frequency_hz or default
    if clamp:
        low, high = clamp
        freq = max(low, min(high, freq))
    return freq


def duration_from_semantics(
    semantics: PromptSemantics,
    *,
    default_ms: float = 1000.0,
    clamp: Sequence[float] | None = (50.0, 10_000.0),
) -> float:
    """Return duration (milliseconds) inferred from semantics."""
    duration = semantics.duration_ms or default_ms
    if clamp:
        low, high = clamp
        duration = max(low, min(high, duration))
    return duration


def append_tags(base: Iterable[str], extras: Iterable[str]) -> List[str]:
    """Merge tag iterables, preserving order and removing duplicates."""
    seen: set[str] = set()
    merged: List[str] = []
    for tag in list(base) + list(extras):
        if not tag:
            continue
        if tag in seen:
            continue
        seen.add(tag)
        merged.append(tag)
    return merged


def envelope_from_intensity(
    semantics: PromptSemantics,
    *,
    base_attack: float = 0.1,
    base_release: float = 1.2,
) -> dict:
    """Construct synth envelope coefficients tuned by prompt intensity."""
    scalar = intensity_scalar(semantics, default=0.7)
    attack = round(base_attack * (1.0 / max(0.35, scalar)), 3)
    decay = round(0.3 * scalar, 3)
    sustain = round(min(0.95, 0.5 + scalar / 2.0), 3)
    release = round(base_release * (1.0 / max(0.35, scalar)), 3)
    return {
        "attack": attack,
        "decay": decay,
        "sustain": sustain,
        "release": release,
    }


def amplitude_from_intensity(semantics: PromptSemantics, *, default: float = 0.8) -> float:
    """Return modulation amplitude based on prompt intensity."""
    value = intensity_scalar(semantics, default=default)
    return round(max(0.1, min(1.0, value)), 3)


def radians_from_tempo(tempo_bpm: float) -> float:
    """Convert BPM to angular frequency for shader oscillation."""
    return round(2.0 * math.pi * max(1.0, tempo_bpm / 60.0), 3)


__all__ = [
    "amplitude_from_intensity",
    "append_tags",
    "duration_from_semantics",
    "ensure_semantics",
    "envelope_from_intensity",
    "frequency_from_semantics",
    "intensity_scalar",
    "radians_from_tempo",
    "sanitize_identifier",
    "tempo_from_semantics",
]
