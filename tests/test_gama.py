"""Tests for Module Gama."""

import pytest
from fractions import Fraction
from src.murbach import alfa, beta
from src.murbach.gama import generate
from tests.conftest import MATRIX_3x3, MATRIX_4x4


class TestGeneration:
    def test_produces_events(self):
        a = alfa.process(MATRIX_3x3)
        b = beta.process(MATRIX_3x3)
        events = generate(a, b, horizon=2)  # shallow horizon for speed
        assert len(events) > 0

    def test_all_pitches_in_scale(self):
        a = alfa.process(MATRIX_4x4)
        b = beta.process(MATRIX_4x4)
        events = generate(a, b, horizon=2)
        for ev in events:
            assert ev.pitch in a.scale, f"Pitch {ev.pitch} not in scale"


class TestTermination:
    def test_ends_on_tonic(self):
        a = alfa.process(MATRIX_4x4)
        b = beta.process(MATRIX_4x4)
        events = generate(a, b, horizon=2)
        assert len(events) > 0
        assert events[-1].pitch == a.T, (
            f"Last pitch {events[-1].pitch} != tonic {a.T}"
        )


class TestMetric:
    def test_no_single_event_exceeds_cap(self):
        a = alfa.process(MATRIX_4x4)
        b = beta.process(MATRIX_4x4)
        events = generate(a, b, horizon=2)
        for ev in events:
            assert ev.duration <= b.cap, (
                f"Duration {ev.duration} exceeds bar capacity {b.cap}"
            )


class TestDeterminism:
    def test_three_runs_identical(self):
        a = alfa.process(MATRIX_3x3)
        b = beta.process(MATRIX_3x3)
        runs = [generate(a, b, horizon=2) for _ in range(3)]
        for i in range(1, 3):
            assert len(runs[i]) == len(runs[0])
            for j in range(len(runs[0])):
                assert runs[i][j].pitch == runs[0][j].pitch
                assert runs[i][j].duration == runs[0][j].duration
                assert runs[i][j].midi_note == runs[0][j].midi_note
