#!/usr/bin/env python3
"""
Método Murbach – Deterministic Algorithmic Composition System.

Usage:
    python -m src.main              # launch GUI
    python -m src.main --headless   # run pipeline, export files, no GUI
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure the project root is on sys.path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _run_headless(matrix: list[list[int]] | None = None) -> None:
    """Run the full pipeline without GUI and export MIDI + WAV."""
    from src.murbach import alfa, beta, audio
    from src.murbach.gama import generate
    from src.murbach.config import NOTE_NAMES, DEFAULT_BPM

    if matrix is None:
        matrix = [
            [3, 1, 4, 1],
            [5, 9, 2, 6],
            [5, 3, 5, 8],
            [9, 7, 9, 3],
        ]

    print(f"Matrix {len(matrix)}×{len(matrix[0])}:")
    for row in matrix:
        print("  ", row)

    print("\n── Module Alfa ──")
    a = alfa.process(matrix)
    print(f"  Tonic: {NOTE_NAMES[a.T]}  Mode: {a.modo}  Scale: {[NOTE_NAMES[p] for p in a.scale]}")
    print(f"  FreqH: {a.freqH}")

    print("\n── Module Beta ──")
    b = beta.process(matrix)
    print(f"  Time sig: {b.C}  Cap: {b.cap}")
    print(f"  Qr: {dict(b.Qr)}")

    print("\n── Module Gama ──")

    def progress(step, total):
        print(f"\r  Generating... {step}/{total}", end="", flush=True)

    events = generate(a, b, callback=progress)
    print(f"\n  Generated {len(events)} events.")

    if events:
        print("\n  First 10 events:")
        for i, ev in enumerate(events[:10]):
            print(f"    {i+1}. {NOTE_NAMES[ev.pitch]}{ev.midi_note // 12 - 1}"
                  f"  dur={ev.duration}  midi={ev.midi_note}")
        last = events[-1]
        print(f"  Last event: {NOTE_NAMES[last.pitch]}{last.midi_note // 12 - 1}"
              f"  dur={last.duration}")

    out = _ROOT / "output"
    mid = audio.events_to_midi(events, bpm=DEFAULT_BPM, ts_str=b.C)
    midi_path = audio.save_midi(mid, out / "output.mid")
    print(f"\n  MIDI → {midi_path}")

    wav_path = audio.events_to_wav(events, out / "output.wav", bpm=DEFAULT_BPM)
    print(f"  WAV  → {wav_path}")
    print("\nDone.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Método Murbach")
    parser.add_argument("--headless", action="store_true",
                        help="Run without GUI (pipeline + export)")
    args = parser.parse_args()

    if args.headless:
        _run_headless()
    else:
        from src.gui.app import run
        run()


if __name__ == "__main__":
    main()
