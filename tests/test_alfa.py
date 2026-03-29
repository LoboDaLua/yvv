"""Tests for Module Alfa."""

import pytest
from src.murbach import alfa
from src.murbach.utils import build_scale, d_circ
from tests.conftest import IDENTITY_3x3, MATRIX_3x3, MATRIX_4x4, SINGULAR_3x3


class TestTonic:
    def test_identity_det1(self):
        out = alfa.process(IDENTITY_3x3)
        # det(I) = 1 → T = 1 (C#), minor (odd)
        assert out.T == 1
        assert out.modo == "min"

    def test_singular_det0(self):
        out = alfa.process(SINGULAR_3x3)
        # det = 0 → T = 0 (C)
        assert out.T == 0

    def test_mode_even_det(self):
        # det of MATRIX_4x4 determines mode
        out = alfa.process(MATRIX_4x4)
        import numpy as np
        det_val = abs(int(round(np.linalg.det(np.array(MATRIX_4x4, dtype=float)))))
        expected_mode = "maj" if det_val % 2 == 0 else "min"
        assert out.modo == expected_mode


class TestScale:
    def test_scale_length(self):
        out = alfa.process(MATRIX_3x3)
        assert len(out.scale) == 7

    def test_scale_contains_tonic(self):
        out = alfa.process(MATRIX_3x3)
        assert out.T in out.scale
        assert out.scale[0] == out.T  # tonic is first degree


class TestProjection:
    def test_all_pitches_in_scale(self):
        out = alfa.process(MATRIX_4x4)
        for row in out.H:
            for pc in row:
                assert pc in out.scale, f"Pitch {pc} not in scale {out.scale}"

    def test_anchor_is_tonic(self):
        out = alfa.process(MATRIX_4x4)
        assert out.H[0][0] == out.T

    def test_freq_sums_to_n_squared(self):
        out = alfa.process(MATRIX_4x4)
        assert sum(out.freqH.values()) == 16  # 4x4


class TestDeterminism:
    def test_same_input_same_output(self):
        a = alfa.process(MATRIX_4x4)
        b = alfa.process(MATRIX_4x4)
        assert a.H == b.H
        assert a.T == b.T
        assert a.modo == b.modo
        assert a.freqH == b.freqH
