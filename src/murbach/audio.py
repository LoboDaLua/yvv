"""
Audio pipeline – MIDI generation, WAV synthesis, and playback.

Supports two synthesis backends:
  1. SoundFont via tinysoundfont (if available + .sf2 present)
  2. Fallback: simple sine-wave synthesis with numpy
"""

from __future__ import annotations

import math
import os
import struct
import threading
import wave
from fractions import Fraction
from pathlib import Path
from typing import Sequence

import numpy as np
import mido

from .config import DEFAULT_BPM, NOTE_NAMES
from .types import Event

# =====================================================================
# MIDI creation
# =====================================================================

TICKS_PER_BEAT = 480  # standard resolution

def _duration_to_ticks(dur: Fraction, ticks_per_beat: int = TICKS_PER_BEAT) -> int:
    """Convert a whole-note fraction to MIDI ticks (quarter = 1 beat)."""
    # dur is in whole-note units: 1/4 = one quarter note = 1 beat
    beats = dur * 4  # quarter-note beats
    return int(beats * ticks_per_beat)


def events_to_midi(
    events: Sequence[Event],
    bpm: int = DEFAULT_BPM,
    ts_str: str = "4/4",
    velocity: int = 80,
) -> mido.MidiFile:
    """Build a single-track MIDI file from *events*."""
    mid = mido.MidiFile(ticks_per_beat=TICKS_PER_BEAT)
    track = mido.MidiTrack()
    mid.tracks.append(track)

    # Tempo meta
    track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(bpm), time=0))

    # Time-signature meta
    num, den = map(int, ts_str.split("/"))
    den_power = int(math.log2(den))
    track.append(mido.MetaMessage(
        "time_signature",
        numerator=num,
        denominator=den_power,
        clocks_per_click=24,
        notated_32nd_notes_per_beat=8,
        time=0,
    ))

    # Program change (piano)
    track.append(mido.Message("program_change", program=0, time=0))

    for ev in events:
        ticks = _duration_to_ticks(ev.duration)
        track.append(mido.Message(
            "note_on", note=ev.midi_note, velocity=velocity, time=0,
        ))
        track.append(mido.Message(
            "note_off", note=ev.midi_note, velocity=0, time=ticks,
        ))

    track.append(mido.MetaMessage("end_of_track", time=0))
    return mid


def save_midi(mid: mido.MidiFile, path: str | Path) -> Path:
    """Write MIDI file to disk and return the path."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    mid.save(str(p))
    return p


# =====================================================================
# WAV synthesis
# =====================================================================

SAMPLE_RATE = 44100
_SOUNDFONTS_DIR = Path(__file__).resolve().parent.parent.parent / "soundfonts"


def _find_soundfont() -> Path | None:
    """Return path to the first .sf2 file found in the soundfonts dir."""
    if not _SOUNDFONTS_DIR.is_dir():
        return None
    # Prefer default.sf2
    default = _SOUNDFONTS_DIR / "default.sf2"
    if default.exists():
        return default
    for f in sorted(_SOUNDFONTS_DIR.glob("*.sf2")):
        return f
    return None


def _render_soundfont(
    events: Sequence[Event],
    sf2_path: Path,
    bpm: int = DEFAULT_BPM,
) -> np.ndarray:
    """Render events to stereo float32 PCM via tinysoundfont (low-level API)."""
    import tinysoundfont._tinysoundfont as tsf

    sf = tsf.SoundFont(str(sf2_path))
    sf.set_output(tsf.OutputMode.StereoInterleaved, SAMPLE_RATE, 0.0)

    # Use preset index 0 (first available instrument)
    sf.channel_set_preset_index(0, 0)

    quarter_sec = 60.0 / bpm
    chunks: list[np.ndarray] = []

    for ev in events:
        dur_sec = float(ev.duration) * 4.0 * quarter_sec
        n_samples = max(int(dur_sec * SAMPLE_RATE), 1)

        sf.note_on(0, ev.midi_note, 0.6)

        # Render note duration
        buf = bytearray(n_samples * 2 * 4)  # stereo interleaved float32
        sf.render(buf, False)
        chunk = np.frombuffer(buf, dtype=np.float32).copy().reshape(-1, 2)
        chunks.append(chunk)

        sf.note_off(0, ev.midi_note)

        # Small release tail (50ms)
        release_n = min(int(0.05 * SAMPLE_RATE), 2205)
        rel_buf = bytearray(release_n * 2 * 4)
        sf.render(rel_buf, False)
        rel_chunk = np.frombuffer(rel_buf, dtype=np.float32).copy().reshape(-1, 2)
        chunks.append(rel_chunk)

    if not chunks:
        return np.zeros((SAMPLE_RATE, 2), dtype=np.float32)
    return np.concatenate(chunks)


def _midi_to_freq(midi_note: int) -> float:
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))


def _render_sine(events: Sequence[Event], bpm: int = DEFAULT_BPM) -> np.ndarray:
    """Render events to a PCM float32 array using additive sine synthesis."""
    quarter_sec = 60.0 / bpm  # seconds per quarter note
    samples: list[np.ndarray] = []

    for ev in events:
        dur_sec = float(ev.duration) * 4.0 * quarter_sec
        n_samples = int(dur_sec * SAMPLE_RATE)
        if n_samples == 0:
            continue
        t = np.linspace(0, dur_sec, n_samples, endpoint=False, dtype=np.float32)
        freq = _midi_to_freq(ev.midi_note)

        # Simple ADSR-ish envelope
        env = np.ones(n_samples, dtype=np.float32)
        attack = min(int(0.01 * SAMPLE_RATE), n_samples)
        release = min(int(0.05 * SAMPLE_RATE), n_samples)
        if attack > 0:
            env[:attack] = np.linspace(0, 1, attack, dtype=np.float32)
        if release > 0:
            env[-release:] = np.linspace(1, 0, release, dtype=np.float32)

        # Fundamental + soft 2nd harmonic
        wave_data = 0.7 * np.sin(2.0 * np.pi * freq * t)
        wave_data += 0.2 * np.sin(4.0 * np.pi * freq * t)
        wave_data *= env * 0.5  # master volume
        samples.append(wave_data)

    if not samples:
        return np.zeros(SAMPLE_RATE, dtype=np.float32)  # 1s silence
    return np.concatenate(samples)


def events_to_wav(
    events: Sequence[Event],
    path: str | Path,
    bpm: int = DEFAULT_BPM,
) -> Path:
    """Render events to a WAV file and return the path.

    Uses SoundFont synthesis if a .sf2 is available in soundfonts/,
    otherwise falls back to sine-wave synthesis.
    """
    sf2 = _find_soundfont()
    if sf2 is not None:
        try:
            pcm = _render_soundfont(events, sf2, bpm)
            stereo = True
        except Exception:
            pcm = _render_sine(events, bpm)
            stereo = False
    else:
        pcm = _render_sine(events, bpm)
        stereo = False

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    pcm_clipped = np.clip(pcm, -1.0, 1.0)
    pcm_16 = (pcm_clipped * 32767).astype(np.int16)

    n_channels = 2 if stereo else 1
    with wave.open(str(p), "wb") as wf:
        wf.setnchannels(n_channels)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm_16.tobytes())

    return p


# =====================================================================
# Playback (non-blocking, stoppable)
# =====================================================================

_stop_event = threading.Event()
_play_thread: threading.Thread | None = None


def play_wav(path: str | Path) -> None:
    """Play a WAV file in a background thread. Call ``stop()`` to interrupt."""
    global _play_thread
    stop()  # stop any previous playback

    _stop_event.clear()

    def _worker():
        try:
            import sounddevice as sd
            import soundfile as sf
            data, sr = sf.read(str(path), dtype="float32")
            sd.play(data, sr)
            # Wait until done or stopped
            while sd.get_stream().active and not _stop_event.is_set():
                sd.sleep(100)
            if _stop_event.is_set():
                sd.stop()
        except Exception:
            pass  # gracefully fail if audio device unavailable

    _play_thread = threading.Thread(target=_worker, daemon=True)
    _play_thread.start()


def stop() -> None:
    """Stop any ongoing playback."""
    _stop_event.set()
    try:
        import sounddevice as sd
        sd.stop()
    except Exception:
        pass


def is_playing() -> bool:
    global _play_thread
    if _play_thread is None:
        return False
    return _play_thread.is_alive()
