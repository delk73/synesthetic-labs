"""Prompt parsing utilities for schema version 0.7.3."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


_MODALITY_KEYWORDS: Mapping[str, str] = {
    "shader": "shader",
    "visual": "shader",
    "fragment": "shader",
    "glsl": "shader",
    "tone": "tone",
    "sound": "tone",
    "audio": "tone",
    "melody": "tone",
    "music": "tone",
    "haptic": "haptic",
    "vibration": "haptic",
    "rumble": "haptic",
    "control": "control",
    "modulation": "modulation",
    "tempo": "modulation",
}

_COLOR_KEYWORDS: Mapping[str, Tuple[float, float, float]] = {
    "red": (1.0, 0.0, 0.0),
    "crimson": (0.86, 0.08, 0.24),
    "scarlet": (1.0, 0.14, 0.0),
    "orange": (1.0, 0.55, 0.0),
    "amber": (1.0, 0.75, 0.0),
    "gold": (1.0, 0.84, 0.0),
    "yellow": (1.0, 0.95, 0.0),
    "green": (0.0, 1.0, 0.0),
    "teal": (0.0, 0.8, 0.7),
    "cyan": (0.0, 1.0, 1.0),
    "aqua": (0.0, 1.0, 0.94),
    "blue": (0.0, 0.0, 1.0),
    "indigo": (0.29, 0.0, 0.51),
    "purple": (0.5, 0.0, 0.5),
    "violet": (0.54, 0.17, 0.89),
    "magenta": (1.0, 0.0, 1.0),
    "pink": (1.0, 0.64, 0.8),
    "white": (1.0, 1.0, 1.0),
    "black": (0.05, 0.05, 0.05),
    "silver": (0.75, 0.75, 0.75),
}

_EFFECT_KEYWORDS = {
    "pulse": "pulse",
    "pulsing": "pulse",
    "heartbeat": "pulse",
    "beat": "pulse",
    "flash": "pulse",
    "wave": "wave",
    "waves": "wave",
    "sine": "wave",
    "oscillate": "wave",
    "flow": "wave",
    "spark": "spark",
    "glow": "glow",
    "bloom": "glow",
    "spiral": "spiral",
    "rotate": "spiral",
    "spin": "spiral",
    "ambient": "ambient",
    "drone": "drone",
    "percussive": "percussive",
    "rhythm": "percussive",
}

_INTENSITY_KEYWORDS = {
    "gentle": "gentle",
    "soft": "gentle",
    "subtle": "gentle",
    "calm": "gentle",
    "smooth": "gentle",
    "warm": "warm",
    "bright": "bright",
    "vibrant": "vibrant",
    "energetic": "energetic",
    "intense": "intense",
    "heavy": "intense",
    "aggressive": "intense",
    "sharp": "sharp",
}

_MOOD_KEYWORDS = {
    "ambient",
    "ethereal",
    "dark",
    "mellow",
    "uplifting",
    "dramatic",
    "soothing",
    "mysterious",
    "dreamy",
    "cinematic",
    "nostalgic",
}

_FREQUENCY_PATTERN = re.compile(
    r"(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>hz|khz|bpm|rpm|hz\.)",
    flags=re.IGNORECASE,
)
_DURATION_PATTERN = re.compile(
    r"(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>ms|s|seconds|second|minutes|beats)",
    flags=re.IGNORECASE,
)
_NUMBER_PATTERN = re.compile(r"\d+(?:\.\d+)?")


@dataclass(frozen=True)
class PromptSemantics:
    """Structured representation of the parsed prompt."""

    raw: str
    modality: str
    colors: Tuple[str, ...] = field(default_factory=tuple)
    effects: Tuple[str, ...] = field(default_factory=tuple)
    intensity: Optional[str] = None
    mood: Optional[str] = None
    tempo_bpm: Optional[float] = None
    frequency_hz: Optional[float] = None
    duration_ms: Optional[float] = None
    numeric_tokens: Tuple[float, ...] = field(default_factory=tuple)
    tags: Tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, object]:
        """Return a JSON-serialisable view of the semantics."""
        return {
            "modality": self.modality,
            "colors": list(self.colors),
            "effects": list(self.effects),
            "intensity": self.intensity,
            "mood": self.mood,
            "tempo_bpm": self.tempo_bpm,
            "frequency_hz": self.frequency_hz,
            "duration_ms": self.duration_ms,
            "numeric_tokens": list(self.numeric_tokens),
            "tags": list(self.tags),
        }


def parse_prompt(prompt: str) -> PromptSemantics:
    """Extract semantic features from *prompt* suitable for component builders."""
    lowered = (prompt or "").strip().lower()
    modality = detect_modality(lowered)
    colors = tuple(_match_keywords(lowered, _COLOR_KEYWORDS.keys()))
    effects = tuple(_match_effects(lowered))
    intensity = _match_first(lowered, _INTENSITY_KEYWORDS)
    mood = _match_mood(lowered)
    tempo = _extract_tempo(lowered)
    frequency = _extract_frequency(lowered)
    duration = _extract_duration(lowered)
    numeric_tokens = tuple(float(match) for match in _NUMBER_PATTERN.findall(lowered))
    tags = tuple(sorted(set(colors + effects)))
    return PromptSemantics(
        raw=prompt,
        modality=modality,
        colors=colors,
        effects=effects,
        intensity=intensity,
        mood=mood,
        tempo_bpm=tempo,
        frequency_hz=frequency,
        duration_ms=duration,
        numeric_tokens=numeric_tokens,
        tags=tags,
    )


def detect_modality(prompt: str) -> str:
    """Infer dominant modality for *prompt*."""
    for keyword, modality in _MODALITY_KEYWORDS.items():
        if keyword in prompt:
            return modality
    if "hz" in prompt or "frequency" in prompt:
        return "tone"
    if "bpm" in prompt or "tempo" in prompt or "beat" in prompt:
        return "modulation"
    if "rumble" in prompt or "vibration" in prompt:
        return "haptic"
    return "shader"


def extract_attributes(prompt: str) -> Dict[str, object]:
    """Return attribute map extracted from *prompt*."""
    semantics = parse_prompt(prompt)
    return semantics.to_dict()


def extract_constraints(prompt: str) -> Dict[str, object]:
    """Return constraint hints (tempo, frequency, duration) from *prompt*."""
    semantics = parse_prompt(prompt)
    constraints: Dict[str, object] = {}
    if semantics.tempo_bpm is not None:
        constraints["tempo_bpm"] = semantics.tempo_bpm
    if semantics.frequency_hz is not None:
        constraints["frequency_hz"] = semantics.frequency_hz
    if semantics.duration_ms is not None:
        constraints["duration_ms"] = semantics.duration_ms
    return constraints


# Internal helpers -----------------------------------------------------

def _match_keywords(prompt: str, candidates: Iterable[str]) -> List[str]:
    matches: List[str] = []
    for candidate in candidates:
        if candidate in prompt:
            matches.append(candidate)
    return matches


def _match_effects(prompt: str) -> List[str]:
    effects: List[str] = []
    for keyword, effect in _EFFECT_KEYWORDS.items():
        if keyword in prompt:
            effects.append(effect)
    seen: set[str] = set()
    deduped: List[str] = []
    for effect in effects:
        if effect in seen:
            continue
        seen.add(effect)
        deduped.append(effect)
    return deduped


def _match_first(prompt: str, mapping: Mapping[str, str]) -> Optional[str]:
    for keyword, value in mapping.items():
        if keyword in prompt:
            return value
    return None


def _match_mood(prompt: str) -> Optional[str]:
    for keyword in _MOOD_KEYWORDS:
        if keyword in prompt:
            return keyword
    return None


def _extract_frequency(prompt: str) -> Optional[float]:
    for match in _FREQUENCY_PATTERN.finditer(prompt):
        value = float(match.group("value"))
        unit = match.group("unit").lower()
        if unit.endswith("bpm"):
            continue
        if unit.startswith("khz"):
            return value * 1000.0
        return value
    return None


def _extract_tempo(prompt: str) -> Optional[float]:
    match = _FREQUENCY_PATTERN.search(prompt)
    if match and match.group("unit").lower().endswith("bpm"):
        return float(match.group("value"))
    if "bpm" in prompt:
        digits = _NUMBER_PATTERN.findall(prompt)
        if digits:
            return float(digits[0])
    return None


def _extract_duration(prompt: str) -> Optional[float]:
    match = _DURATION_PATTERN.search(prompt)
    if not match:
        return None
    value = float(match.group("value"))
    unit = match.group("unit").lower()
    if unit in {"s", "second", "seconds"}:
        return value * 1000.0
    if unit == "minutes":
        return value * 60_000.0
    if unit == "beats":
        # Interpret beats as tempo-relative; caller can convert.
        return value
    return value


__all__ = [
    "PromptSemantics",
    "parse_prompt",
    "detect_modality",
    "extract_attributes",
    "extract_constraints",
]
