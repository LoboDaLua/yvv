"""
Módulo Alfa – Tonal Extraction and Diatonic Structuring.

Takes an integer matrix A and produces a diatonic pitch-class matrix H
along with tonic, mode, scale, and frequency stock.
"""

from __future__ import annotations

import numpy as np

from .config import DEGREE_PRIORITY
from .types import AlfaOutput
from .utils import build_scale, d_circ, degree_of, degree_priority


def _nearest_in_scale(
    pitch: int,
    scale: list[int],
    freq: dict[int, int],
) -> int:
    """Map *pitch* to the nearest scale member.

    Tie-break rules (deterministic, no RNG):
      1. Fewer occurrences in the partial stock built so far.
      2. Higher structural-hierarchy priority (I ≻ V ≻ III …).
    """
    best: list[int] = []
    best_dist = 13  # worse than any circular distance

    for s in scale:
        d = d_circ(pitch, s)
        if d < best_dist:
            best_dist = d
            best = [s]
        elif d == best_dist:
            best.append(s)

    if len(best) == 1:
        return best[0]

    # Tie-break 1: fewest occurrences so far
    min_count = min(freq.get(s, 0) for s in best)
    best = [s for s in best if freq.get(s, 0) == min_count]
    if len(best) == 1:
        return best[0]

    # Tie-break 2: highest structural-hierarchy weight
    best.sort(key=lambda s: degree_priority(degree_of(s, scale)), reverse=True)
    return best[0]


def process(A: list[list[int]]) -> AlfaOutput:
    """Run Module Alfa on integer matrix *A*.

    Returns an :class:`AlfaOutput` with the projected diatonic matrix,
    tonic, mode, scale, and pitch-class frequency map.
    """
    arr = np.array(A, dtype=float)
    n = arr.shape[0]
    det_val = abs(int(round(np.linalg.det(arr))))

    # 1. Tonic
    T = det_val % 12

    # 2. Mode
    modo = "maj" if det_val % 2 == 0 else "min"

    # 3. Scale
    scale = build_scale(T, modo)

    # 4. Chromatic reduction
    A_pc = [[int(A[i][j]) % 12 for j in range(n)] for i in range(n)]

    # 5. Diatonic projection (row-major, incremental stock tracking)
    freq: dict[int, int] = {s: 0 for s in scale}
    H: list[list[int]] = [[0] * n for _ in range(n)]

    for i in range(n):
        for j in range(n):
            x = A_pc[i][j]
            if x in freq:          # already diatonic
                y = x
            else:
                y = _nearest_in_scale(x, scale, freq)
            H[i][j] = y
            freq[y] = freq.get(y, 0) + 1

    # 6. Anchor: first cell must be the tonic
    old = H[0][0]
    if old != T:
        freq[old] -= 1
        H[0][0] = T
        freq[T] = freq.get(T, 0) + 1

    return AlfaOutput(H=H, T=T, modo=modo, scale=scale, freqH=freq)
