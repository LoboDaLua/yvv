"""
Módulo Gama – The Sequencer Engine.

Consumes the outputs of Alfa and Beta and deterministically generates
a monophonic melody as a sequence of ``Event`` objects.
"""

from __future__ import annotations

import copy
import math
from fractions import Fraction
from typing import Sequence

from .config import (
    BEAM_K,
    CONT_BONUS_MELODY,
    DEGREE_PRIORITY,
    GAMMA,
    HORIZON,
    LAMBDA,
    MIDI_HIGH,
    MIDI_LOW,
    OMEGA_NUC,
    OMEGA_PER,
    PENALTY_CAD,
    PHASE_CAD,
    PHASE_CAD_TRIGGER,
    PHASE_INI,
    PHASE_MED,
    PHASE_MED_TRIGGER,
    POLAR_CYCLE,
    POLAR_TRIADS,
    R0,
    SEMIFRASE_LEN,
    THETA_N,
    THETA_R,
)
from .types import AlfaOutput, BetaOutput, Event, GamaState
from .utils import (
    build_scale,
    d_circ,
    degree_of,
    degree_priority,
    dynamic_d_max,
    dynamic_rho_max,
    melody_continuity_bonus,
    rhythm_continuity_bonus,
    tension_curve,
)


# =====================================================================
# State initialisation
# =====================================================================

def _init_state(alfa: AlfaOutput, beta: BetaOutput) -> GamaState:
    """Create the initial sequencer state from Alfa + Beta outputs."""
    Qn = dict(alfa.freqH)
    Qr = {k: v for k, v in beta.Qr.items()}
    midi_start = _closest_midi(alfa.T, (MIDI_LOW + MIDI_HIGH) // 2)
    return GamaState(
        Qn=Qn,
        Qr=Qr,
        total_notes=sum(Qn.values()),
        total_rhythms=sum(Qr.values()),
        M_t=Fraction(0),
        phase=PHASE_INI,
        polar_idx=0,
        semifrase_counter=0,
        last_note=alfa.T,
        last_rhythm=None,
        last_midi=midi_start,
        events=[],
    )


# =====================================================================
# Helpers
# =====================================================================

def _closest_midi(pc: int, ref: int) -> int:
    """Return the MIDI note number for *pc* closest to *ref* within range."""
    best = None
    best_dist = 999
    for octave in range(MIDI_LOW // 12, MIDI_HIGH // 12 + 1):
        m = octave * 12 + pc
        if MIDI_LOW <= m <= MIDI_HIGH and abs(m - ref) < best_dist:
            best_dist = abs(m - ref)
            best = m
    return best if best is not None else (MIDI_LOW // 12) * 12 + pc


def _consumption(st: GamaState) -> float:
    """Fraction of total stock consumed so far."""
    used_n = st.total_notes - sum(st.Qn.values())
    used_r = st.total_rhythms - sum(st.Qr.values())
    denom = st.total_notes + st.total_rhythms
    if denom == 0:
        return 1.0
    return (used_n + used_r) / denom


def _progress(st: GamaState) -> float:
    """Progress x_t ∈ [0,1] through current structural phase."""
    return min(_consumption(st), 1.0)


def _update_phase(st: GamaState) -> None:
    c = _consumption(st)
    if c > PHASE_CAD_TRIGGER:
        st.phase = PHASE_CAD
    elif c > PHASE_MED_TRIGGER:
        st.phase = PHASE_MED


def _update_polarisation(st: GamaState) -> None:
    st.semifrase_counter += 1
    if st.semifrase_counter >= SEMIFRASE_LEN:
        st.semifrase_counter = 0
        st.polar_idx = (st.polar_idx + 1) % len(POLAR_CYCLE)


def _current_polar(st: GamaState) -> str:
    return POLAR_CYCLE[st.polar_idx]


# =====================================================================
# Hard filter  (§2.1)
# =====================================================================

Candidate = tuple[int, Fraction]  # (pitch_class, duration)


def _hard_filter(
    st: GamaState,
    scale: list[int],
    cap: Fraction,
) -> list[Candidate]:
    """Return all valid (note, rhythm) pairs at the current step."""
    x_t = _progress(st)
    t_val = tension_curve(x_t)
    d_max = dynamic_d_max(t_val)
    rho_max = dynamic_rho_max(t_val)

    candidates: list[Candidate] = []
    for n in scale:
        if st.Qn.get(n, 0) <= 0:
            continue
        # melodic distance constraint
        if d_circ(n, st.last_note) > d_max:
            continue
        for r in R0:
            if st.Qr.get(r, 0) <= 0:
                continue
            # metric fit
            if st.M_t + r > cap:
                continue
            # rhythmic variation
            if st.last_rhythm is not None and abs(r - st.last_rhythm) > rho_max:
                continue
            candidates.append((n, r))
    return candidates


def _relaxed_filter(
    st: GamaState,
    scale: list[int],
    cap: Fraction,
) -> list[Candidate]:
    """Fallback filter with relaxed constraints (deadlock handler)."""
    candidates: list[Candidate] = []
    for n in scale:
        if st.Qn.get(n, 0) <= 0:
            continue
        for r in R0:
            if st.Qr.get(r, 0) <= 0:
                continue
            if st.M_t + r > cap:
                continue
            candidates.append((n, r))
    return candidates


# =====================================================================
# Local scoring  (§2.2)
# =====================================================================

def _f_note(
    n: int,
    st: GamaState,
    scale: list[int],
    tonic: int,
) -> float:
    deg = degree_of(n, scale)
    # W_G – global degree weight
    w_g = degree_priority(deg) if deg is not None else 0.0

    # W_L – local polarisation weight
    polar_key = _current_polar(st)
    polar_set = POLAR_TRIADS[polar_key]
    w_l = OMEGA_NUC if (deg is not None and deg in polar_set) else OMEGA_PER

    # B_C – melodic continuity
    b_c = melody_continuity_bonus(d_circ(n, st.last_note))

    # B_F – phase bonus
    b_f = 0.0
    if st.phase == PHASE_CAD:
        # Cadential: reward tonic cluster {I, III, V}
        if deg is not None and deg in {0, 2, 4}:
            b_f = 1.0
    elif st.phase == PHASE_INI:
        if deg is not None and deg in {0, 2, 4}:
            b_f = 1.0
    else:
        b_f = 0.5  # med – neutral

    return w_g + w_l + b_c + b_f


def _f_rhythm(
    r: Fraction,
    st: GamaState,
    cap: Fraction,
) -> float:
    b_r = 2.0

    # B_M – metric fit
    b_m = 2.0 if st.M_t + r <= cap else 0.0

    # B_Cr – rhythmic continuity
    if st.last_rhythm is not None:
        b_cr = rhythm_continuity_bonus(abs(r - st.last_rhythm))
    else:
        b_cr = 2.0  # first event – neutral bonus

    # B_Fr – phase-rhythm bonus
    b_fr = 0.0
    if st.phase == PHASE_CAD and r >= Fraction(1, 2):
        b_fr = 2.0

    return b_r + b_m + b_cr + b_fr


def _penalties(
    n: int,
    r: Fraction,
    st: GamaState,
    scale: list[int],
    cap: Fraction,
    tonic: int,
) -> float:
    p = 0.0

    # P_est – low-stock penalty
    if st.Qn.get(n, 0) <= THETA_N:
        p += 1.0
    if st.Qr.get(r, 0) <= THETA_R:
        p += 1.0

    # P_cond – abrupt jump
    dist = d_circ(n, st.last_note)
    if dist >= 5:
        p += float(dist - 4)

    # P_met – near bar boundary but not filling it
    remaining = cap - st.M_t
    if remaining - r > Fraction(0) and remaining - r < Fraction(1, 8):
        p += 1.0

    # P_cad – cadential penalty
    if st.phase == PHASE_CAD:
        if n != tonic:
            p += PENALTY_CAD
        if r < Fraction(1, 2):
            p += PENALTY_CAD * 0.5

    return p


def _f_loc(
    n: int,
    r: Fraction,
    st: GamaState,
    scale: list[int],
    cap: Fraction,
    tonic: int,
) -> float:
    return (
        _f_note(n, st, scale, tonic)
        + _f_rhythm(r, st, cap)
        - _penalties(n, r, st, scale, cap, tonic)
    )


# =====================================================================
# Lookahead (DFS with beam pruning)  (§2.3)
# =====================================================================

def _apply_event(st: GamaState, n: int, r: Fraction, cap: Fraction) -> None:
    """Mutate *st* in-place: consume stock and advance metric accumulator."""
    st.Qn[n] -= 1
    st.Qr[r] -= 1
    st.M_t += r
    if st.M_t >= cap:
        st.M_t = Fraction(0)
    st.last_note = n
    st.last_rhythm = r
    _update_phase(st)
    _update_polarisation(st)


def _lookahead(
    st: GamaState,
    scale: list[int],
    cap: Fraction,
    tonic: int,
    depth: int,
    gamma: float,
) -> float:
    """Recursive DFS with beam pruning; returns best discounted future value."""
    if depth <= 0:
        return 0.0

    candidates = _hard_filter(st, scale, cap)
    if not candidates:
        return 0.0

    # Score and keep top-K
    scored = []
    for n, r in candidates:
        scored.append((_f_loc(n, r, st, scale, cap, tonic), n, r))
    scored.sort(key=lambda t: t[0], reverse=True)
    scored = scored[:BEAM_K]

    best = -math.inf
    for local_score, n, r in scored:
        clone = _clone_state_light(st)
        _apply_event(clone, n, r, cap)
        future = _lookahead(clone, scale, cap, tonic, depth - 1, gamma)
        total = local_score + gamma * future
        if total > best:
            best = total

    return best if best > -math.inf else 0.0


def _clone_state_light(st: GamaState) -> GamaState:
    """Shallow clone sufficient for lookahead (skips events list)."""
    return GamaState(
        Qn=dict(st.Qn),
        Qr=dict(st.Qr),
        total_notes=st.total_notes,
        total_rhythms=st.total_rhythms,
        M_t=st.M_t,
        phase=st.phase,
        polar_idx=st.polar_idx,
        semifrase_counter=st.semifrase_counter,
        last_note=st.last_note,
        last_rhythm=st.last_rhythm,
        last_midi=st.last_midi,
        events=[],  # not needed in lookahead
    )


# =====================================================================
# Deterministic selection with lexicographic tie-break  (§2.4)
# =====================================================================

def _select_best(
    scored: list[tuple[float, int, Fraction]],
    st: GamaState,
    scale: list[int],
) -> tuple[int, Fraction]:
    """Pick the best (note, rhythm) from scored candidates.

    Tie-break order (lexicographic, no RNG):
      1. Higher total score  (already the primary sort key)
      2. Higher structural-hierarchy priority  (DEGREE_PRIORITY)
      3. Smaller melodic distance to last note
      4. Smaller rhythmic difference to last rhythm
    """
    eps = 1e-9

    def sort_key(item: tuple[float, int, Fraction]):
        score, n, r = item
        deg = degree_of(n, scale)
        prio = degree_priority(deg)
        mel_dist = d_circ(n, st.last_note)
        rhy_diff = abs(r - (st.last_rhythm or r))
        # We want: max score → max prio → min mel_dist → min rhy_diff
        return (-score, -prio, mel_dist, float(rhy_diff))

    scored.sort(key=sort_key)
    _, n, r = scored[0]
    return n, r


# =====================================================================
# Octave assignment
# =====================================================================

def _assign_octave(pc: int, last_midi: int) -> int:
    """Choose the MIDI note for *pc* closest to *last_midi*, within range."""
    return _closest_midi(pc, last_midi)


# =====================================================================
# Main generator loop  (§2.5 + main loop)
# =====================================================================

def generate(
    alfa: AlfaOutput,
    beta: BetaOutput,
    *,
    horizon: int = HORIZON,
    gamma: float = GAMMA,
    lam: float = LAMBDA,
    omega_nuc: float = OMEGA_NUC,
    omega_per: float = OMEGA_PER,
    beam_k: int = BEAM_K,
    callback=None,
) -> list[Event]:
    """Run the Gama sequencer and return the melodic event list.

    Parameters
    ----------
    alfa, beta : module outputs
    horizon, gamma, lam, omega_nuc, omega_per, beam_k :
        Overridable hyperparameters (defaults from config).
    callback : optional callable(step, total_approx)
        Called after each event for progress reporting.
    """
    # Patch module-level constants for this run (only affects local scoring
    # via closure – we pass them through)
    # We use a simple override by monkey-patching the module-level names
    # only within this function scope via a config dict.
    _cfg = {
        "horizon": horizon,
        "gamma": gamma,
        "lam": lam,
        "omega_nuc": omega_nuc,
        "omega_per": omega_per,
        "beam_k": beam_k,
    }

    scale = alfa.scale
    tonic = alfa.T
    cap = beta.cap

    st = _init_state(alfa, beta)
    approx_total = st.total_notes  # rough upper bound on events

    step = 0
    max_steps = st.total_notes + st.total_rhythms  # safety cap

    while step < max_steps:
        # Check termination: both stocks empty
        if sum(st.Qn.values()) <= 0 or sum(st.Qr.values()) <= 0:
            break

        # ── STEP 2.1: Hard filter ──
        candidates = _hard_filter(st, scale, cap)

        # Deadlock: relax constraints
        if not candidates:
            candidates = _relaxed_filter(st, scale, cap)
        if not candidates:
            # Truly stuck – force new bar and retry once
            st.M_t = Fraction(0)
            candidates = _relaxed_filter(st, scale, cap)
        if not candidates:
            break  # no possible moves at all

        # ── STEP 2.2 + 2.3: Score with local + lookahead ──
        scored: list[tuple[float, int, Fraction]] = []
        for n, r in candidates:
            local = _f_loc(n, r, st, scale, cap, tonic)
            # Lookahead
            clone = _clone_state_light(st)
            _apply_event(clone, n, r, cap)
            future = _lookahead(
                clone, scale, cap, tonic,
                _cfg["horizon"] - 1, _cfg["gamma"],
            )
            total = local + _cfg["lam"] * future
            scored.append((total, n, r))

        # ── STEP 2.4: Select best ──
        best_n, best_r = _select_best(scored, st, scale)

        # ── Apply event ──
        midi = _assign_octave(best_n, st.last_midi)
        ev = Event(pitch=best_n, duration=best_r, midi_note=midi)
        st.events.append(ev)

        st.Qn[best_n] -= 1
        st.Qr[best_r] -= 1
        st.M_t += best_r
        if st.M_t >= cap:
            st.M_t = Fraction(0)
        st.last_note = best_n
        st.last_rhythm = best_r
        st.last_midi = midi
        _update_phase(st)
        _update_polarisation(st)

        step += 1
        if callback:
            callback(step, approx_total)

    # ── STEP 2.5: Forced cadential ending ──
    _force_final_tonic(st, scale, tonic, cap)

    return st.events


def _force_final_tonic(
    st: GamaState,
    scale: list[int],
    tonic: int,
    cap: Fraction,
) -> None:
    """Ensure the final event is the tonic with a long duration."""
    if not st.events:
        return
    last = st.events[-1]
    if last.pitch == tonic:
        return
    # Replace last event's pitch with tonic (keep duration)
    midi = _assign_octave(tonic, st.last_midi)
    st.events[-1] = Event(pitch=tonic, duration=last.duration, midi_note=midi)
