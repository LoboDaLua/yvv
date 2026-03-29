"""
Método Murbach – Data types shared across modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction


@dataclass
class AlfaOutput:
    """Result of Module Alfa (tonal extraction)."""
    H: list[list[int]]             # diatonic-projected pitch-class matrix
    T: int                         # tonic (0–11)
    modo: str                      # 'maj' or 'min'
    scale: list[int]               # 7 pitch classes of the global scale
    freqH: dict[int, int]          # pitch-class → occurrence count in H


@dataclass
class BetaOutput:
    """Result of Module Beta (temporal quantisation)."""
    C: str                         # time-signature string e.g. '3/4'
    cap: Fraction                  # bar capacity as Fraction
    T_beta: list[list[Fraction]]   # duration matrix
    Qr: dict[Fraction, int]        # duration → occurrence count


@dataclass
class Event:
    """A single musical event (one note in the melody)."""
    pitch: int          # pitch class 0–11
    duration: Fraction  # duration as Fraction of a whole note
    midi_note: int = 0  # absolute MIDI note number (set by octave assigner)


@dataclass
class GamaState:
    """Mutable state carried across each step of the Gama sequencer."""
    Qn: dict[int, int]              # remaining note stock
    Qr: dict[Fraction, int]         # remaining rhythm stock
    total_notes: int                # initial sum(Qn)
    total_rhythms: int              # initial sum(Qr)
    M_t: Fraction                   # metric accumulator in current bar
    phase: str                      # 'ini' | 'med' | 'cad'
    polar_idx: int                  # index into POLAR_CYCLE
    semifrase_counter: int          # events since last polarisation change
    last_note: int                  # previous pitch class (starts as T)
    last_rhythm: Fraction | None    # previous duration (None at t=0)
    last_midi: int                  # previous absolute MIDI note
    events: list[Event] = field(default_factory=list)
