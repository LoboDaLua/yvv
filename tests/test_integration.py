"""Integration tests – full pipeline from matrix to audio files."""

import pytest
from pathlib import Path
from fractions import Fraction

from src.murbach import alfa, beta, audio
from src.murbach.gama import generate
from src.murbach.config import NOTE_NAMES
from tests.conftest import MATRIX_3x3, MATRIX_4x4


OUTPUT = Path(__file__).resolve().parent.parent / "output"


class TestFullPipeline:
    def test_matrix_to_events(self):
        a = alfa.process(MATRIX_4x4)
        b = beta.process(MATRIX_4x4)
        events = generate(a, b, horizon=2)
        assert len(events) > 0
        # All pitches diatonic
        for ev in events:
            assert ev.pitch in a.scale
        # Ends on tonic
        assert events[-1].pitch == a.T

    def test_midi_export(self, tmp_path):
        a = alfa.process(MATRIX_3x3)
        b = beta.process(MATRIX_3x3)
        events = generate(a, b, horizon=2)
        mid = audio.events_to_midi(events, bpm=120, ts_str=b.C)
        p = audio.save_midi(mid, tmp_path / "test.mid")
        assert p.exists()
        assert p.stat().st_size > 0

    def test_wav_export(self, tmp_path):
        a = alfa.process(MATRIX_3x3)
        b = beta.process(MATRIX_3x3)
        events = generate(a, b, horizon=2)
        p = audio.events_to_wav(events, tmp_path / "test.wav", bpm=120)
        assert p.exists()
        assert p.stat().st_size > 1000  # should have actual audio data

    def test_determinism_full(self):
        """Two full pipeline runs produce byte-identical event lists."""
        for mat in [MATRIX_3x3, MATRIX_4x4]:
            e1 = generate(alfa.process(mat), beta.process(mat), horizon=2)
            e2 = generate(alfa.process(mat), beta.process(mat), horizon=2)
            assert len(e1) == len(e2)
            for a, b_ in zip(e1, e2):
                assert a.pitch == b_.pitch
                assert a.duration == b_.duration
                assert a.midi_note == b_.midi_note
