"""
Método Murbach – Shared utility functions.
"""

from __future__ import annotations

import math
from fractions import Fraction

from .config import (
    MAJOR_INTERVALS,
    MINOR_INTERVALS,
    DEGREE_PRIORITY,
    CONT_BONUS_MELODY,
    CONT_BONUS_RHYTHM_THRESHOLDS,
)


# ── pitch helpers ───────────────────────────────────────────────────

def d_circ(a: int, b: int) -> int:
    """Circular distance on ℤ₁₂."""
    diff = abs(a - b) % 12
    return min(diff, 12 - diff)


def build_scale(tonic: int, modo: str) -> list[int]:
    """Return the 7 pitch classes of the diatonic scale rooted at *tonic*."""
    template = MAJOR_INTERVALS if modo == "maj" else MINOR_INTERVALS
    return [(tonic + iv) % 12 for iv in template]


def degree_of(pitch: int, scale: list[int]) -> int | None:
    """Return the scale-degree index (0–6) of *pitch*, or None if not in scale."""
    try:
        return scale.index(pitch)
    except ValueError:
        return None


def degree_priority(degree: int | None) -> int:
    """Structural-hierarchy weight for a degree index."""
    if degree is None:
        return -1
    return DEGREE_PRIORITY.get(degree, 0)


# ── tension / dynamics ──────────────────────────────────────────────

def tension_curve(x: float) -> float:
    """Cosine tension curve  T(x) = 0.5·(1 − cos(2πx)),  x ∈ [0, 1]."""
    return 0.5 * (1.0 - math.cos(2.0 * math.pi * x))


def dynamic_d_max(tension: float) -> int:
    """Maximum allowed melodic jump (in scale-degree steps) given tension."""
    return 2 + int(4 * tension)   # range 2 … 6


def dynamic_rho_max(tension: float) -> Fraction:
    """Maximum allowed rhythmic change given tension."""
    # range Fraction(1,8) … Fraction(1,2)
    return Fraction(1, 8) + Fraction(int(tension * 3), 8)


# ── scoring helpers ─────────────────────────────────────────────────

def melody_continuity_bonus(dist: int) -> int:
    """Bonus for melodic proximity to previous note."""
    return CONT_BONUS_MELODY.get(dist, 0)


def rhythm_continuity_bonus(diff: Fraction) -> int:
    """Bonus for rhythmic proximity to previous duration."""
    for threshold, bonus in CONT_BONUS_RHYTHM_THRESHOLDS:
        if diff <= threshold:
            return bonus
    return 0
