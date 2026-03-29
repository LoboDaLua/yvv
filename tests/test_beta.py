"""Tests for Module Beta."""

import pytest
from fractions import Fraction
from src.murbach import beta
from src.murbach.config import TS_MAP, ts_capacity
from tests.conftest import MATRIX_3x3, MATRIX_4x4, SINGULAR_3x3


class TestTimeSignature:
    def test_all_six_mappings(self):
        for m, ts_str in TS_MAP.items():
            cap = ts_capacity(ts_str)
            assert cap > 0

    def test_singular_matrix(self):
        out = beta.process(SINGULAR_3x3)
        # det = 0, mod 6 = 0 → "2/4"
        assert out.C == "2/4"
        assert out.cap == Fraction(2, 4)


class TestCapping:
    def test_no_duration_exceeds_cap(self):
        out = beta.process(MATRIX_4x4)
        for row in out.T_beta:
            for dur in row:
                assert dur <= out.cap, f"Duration {dur} > cap {out.cap}"

    def test_durations_are_valid(self):
        valid = {Fraction(1, 8), Fraction(1, 4), Fraction(1, 2), Fraction(1, 1)}
        out = beta.process(MATRIX_3x3)
        for row in out.T_beta:
            for dur in row:
                assert dur in valid or dur <= out.cap


class TestStock:
    def test_qr_sums_to_n_squared(self):
        out = beta.process(MATRIX_4x4)
        assert sum(out.Qr.values()) == 16

    def test_qr_sums_3x3(self):
        out = beta.process(MATRIX_3x3)
        assert sum(out.Qr.values()) == 9


class TestDeterminism:
    def test_same_input_same_output(self):
        a = beta.process(MATRIX_4x4)
        b = beta.process(MATRIX_4x4)
        assert a.C == b.C
        assert a.cap == b.cap
        assert a.Qr == b.Qr
        for i in range(len(a.T_beta)):
            assert a.T_beta[i] == b.T_beta[i]
