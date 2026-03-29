"""
Método Murbach – Constants and Hyperparameters

All tuneable values and structural constants live here so the rest
of the codebase never hard-codes magic numbers.
"""

from fractions import Fraction

# ── Pitch-class universe ────────────────────────────────────────────
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F",
              "F#", "G", "G#", "A", "A#", "B"]

# Intervallic templates (semitones from tonic)
MAJOR_INTERVALS = [0, 2, 4, 5, 7, 9, 11]
MINOR_INTERVALS = [0, 2, 3, 5, 7, 8, 10]

# Structural‑hierarchy weights  (scale‑degree index → weight)
# I=0  II=1  III=2  IV=3  V=4  VI=5  VII=6
DEGREE_PRIORITY = {0: 4, 4: 3, 2: 2, 3: 2, 1: 1, 5: 1, 6: 0}

# ── Rhythmic vocabulary ─────────────────────────────────────────────
R0 = [Fraction(1, 8), Fraction(1, 4), Fraction(1, 2), Fraction(1, 1)]

# Duration ↔ mod‑4 mapping  (Beta module)
DUR_MAP = {
    0: Fraction(1, 8),
    1: Fraction(1, 4),
    2: Fraction(1, 2),
    3: Fraction(1, 1),
}

# ── Time‑signature map  (|det| mod 6 → string) ─────────────────────
TS_MAP = {
    0: "2/4",
    1: "3/4",
    2: "4/4",
    3: "6/8",
    4: "9/8",
    5: "12/8",
}


def ts_capacity(ts_str: str) -> Fraction:
    """Return the *total beat-value* of one bar as a Fraction.

    For simple metres the numerator counts quarter-note beats;
    for compound metres each denominator-unit is an eighth-note,
    but we express everything in whole-note fractions so that
    1 = semibreve, 1/2 = minim, 1/4 = crotchet, 1/8 = quaver.
    """
    num, den = map(int, ts_str.split("/"))
    return Fraction(num, den)


# ── Gama – hyperparameters ──────────────────────────────────────────
HORIZON = 5          # lookahead depth  (h)
GAMMA = 0.9          # discount factor  (γ)
LAMBDA = 0.5         # future-weight    (λ)
OMEGA_NUC = 3.0      # local-nucleus weight  (ω_nuc)
OMEGA_PER = 1.0      # local-periphery weight (ω_per)
THETA_N = 2          # note-scarcity threshold (θ_n)
THETA_R = 2          # rhythm-scarcity threshold (θ_r)
BEAM_K = 8           # beam-width for lookahead pruning

SEMIFRASE_LEN = 8    # events per semifrase unit

# Polarisation triads  (scale-degree indices)
POLAR_TRIADS = {
    "I":  {0, 2, 4},   # I  III  V
    "IV": {3, 5, 0},   # IV VI   I
    "V":  {4, 6, 1},   # V  VII  II
}
POLAR_CYCLE = ["I", "IV", "V", "I"]

# Continuity-bonus table  (melodic distance → bonus)
CONT_BONUS_MELODY = {0: 2, 1: 2, 2: 2, 3: 1, 4: 1}   # ≥5 → 0

# Continuity-bonus table  (rhythmic difference → bonus)
# keys are Fraction thresholds, evaluated with <=
CONT_BONUS_RHYTHM_THRESHOLDS = [
    (Fraction(1, 8), 2),
    (Fraction(1, 4), 1),
]

# Phase names
PHASE_INI = "ini"
PHASE_MED = "med"
PHASE_CAD = "cad"

# Phase trigger thresholds (fraction consumed)
PHASE_MED_TRIGGER = 0.25
PHASE_CAD_TRIGGER = 0.75

# Cadential penalty applied when note ≠ tonic or rhythm is short
PENALTY_CAD = 10.0

# Default BPM for MIDI export
DEFAULT_BPM = 120

# MIDI pitch range for octave assignment
MIDI_LOW = 60    # C4
MIDI_HIGH = 84   # C6
