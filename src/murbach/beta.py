"""
Módulo Beta – Temporal Quantisation.

Takes an integer matrix P and produces a duration matrix T_beta
along with time-signature, bar capacity, and rhythm stock.
"""

from __future__ import annotations

from fractions import Fraction

import numpy as np

from .config import DUR_MAP, TS_MAP, ts_capacity
from .types import BetaOutput


def process(P: list[list[int]]) -> BetaOutput:
    """Run Module Beta on integer matrix *P*.

    Returns a :class:`BetaOutput` with time-signature info,
    the quantised duration matrix, and rhythm-stock counts.
    """
    arr = np.array(P, dtype=float)
    n = arr.shape[0]
    det_val = abs(int(round(np.linalg.det(arr))))

    # 1. Time signature
    m = det_val % 6
    C = TS_MAP[m]
    cap = ts_capacity(C)

    # 2. Mod-4 reduction → duration mapping
    T_beta: list[list[Fraction]] = [[Fraction(0)] * n for _ in range(n)]
    Qr: dict[Fraction, int] = {}

    for i in range(n):
        for j in range(n):
            e = int(P[i][j]) % 4
            dur = DUR_MAP[e]
            # 3. Capping: no duration exceeds the bar capacity
            dur = min(dur, cap)
            T_beta[i][j] = dur
            Qr[dur] = Qr.get(dur, 0) + 1

    return BetaOutput(C=C, cap=cap, T_beta=T_beta, Qr=Qr)
