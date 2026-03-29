"""Integration tests – full pipeline from matrix to audio files."""

import pytest
from pathlib import Path
from fractions import Fraction

from src.murbach import alfa, beta, audio
from src.murbach.gama import generate
from src.murbach.config import NOTE_NAMES
from src.gui.matrix_editor import load_matrix_from_csv, save_matrix_to_csv
from tests.conftest import MATRIX_3x3, MATRIX_4x4, MATRIX_6x6


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


class TestVariableSizeMatrix:
    def test_6x6_pipeline(self):
        a = alfa.process(MATRIX_6x6)
        b = beta.process(MATRIX_6x6)
        events = generate(a, b, horizon=2)
        assert len(events) > 0
        for ev in events:
            assert ev.pitch in a.scale
        assert events[-1].pitch == a.T

    def test_2x2_pipeline(self):
        mat = [[7, 3], [2, 5]]
        a = alfa.process(mat)
        b = beta.process(mat)
        events = generate(a, b, horizon=2)
        assert len(events) > 0

    def test_8x8_pipeline(self):
        mat = [[(i * 7 + j * 3 + 1) % 10 for j in range(8)] for i in range(8)]
        a = alfa.process(mat)
        b = beta.process(mat)
        events = generate(a, b, horizon=1)
        assert len(events) > 0
        for ev in events:
            assert ev.pitch in a.scale


class TestCSVRoundTrip:
    def test_export_import_identity(self, tmp_path):
        for mat in [MATRIX_3x3, MATRIX_4x4, MATRIX_6x6]:
            p = save_matrix_to_csv(mat, tmp_path / "mat.csv")
            loaded = load_matrix_from_csv(p)
            assert loaded == mat

    def test_csv_file_contents(self, tmp_path):
        p = save_matrix_to_csv(MATRIX_3x3, tmp_path / "test.csv")
        text = p.read_text()
        assert "2,7,1" in text
        assert "5,3,8" in text

    def test_pipeline_after_csv_roundtrip(self, tmp_path):
        p = save_matrix_to_csv(MATRIX_4x4, tmp_path / "rt.csv")
        loaded = load_matrix_from_csv(p)
        a = alfa.process(loaded)
        b = beta.process(loaded)
        events = generate(a, b, horizon=2)
        # Should produce identical results to direct processing
        a2 = alfa.process(MATRIX_4x4)
        b2 = beta.process(MATRIX_4x4)
        events2 = generate(a2, b2, horizon=2)
        assert len(events) == len(events2)
        for e1, e2 in zip(events, events2):
            assert e1.pitch == e2.pitch
            assert e1.duration == e2.duration
