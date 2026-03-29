"""
Main Dear PyGui application – wires matrix editor, pipeline, piano roll,
score view, and controls together.
"""

from __future__ import annotations

import threading
from pathlib import Path

import dearpygui.dearpygui as dpg

from ..murbach import alfa, beta, audio
from ..murbach.gama import generate
from ..murbach.config import NOTE_NAMES
from ..murbach.types import Event

from . import controls, matrix_editor, piano_roll, score_view

# ── Module-level state ──────────────────────────────────────────────

_events: list[Event] = []
_alfa_out = None
_beta_out = None
_midi_file = None
_wav_file = None
_OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "output"


# ── Callbacks ───────────────────────────────────────────────────────

def _on_generate(sender=None, app_data=None, user_data=None):
    global _events, _alfa_out, _beta_out, _midi_file, _wav_file
    _midi_file = None
    _wav_file = None

    mat = matrix_editor.get_matrix()
    hp = controls.get_hyperparams()

    controls.set_status("Running Alfa...")
    controls.set_progress(0.05, "Alfa")

    try:
        _alfa_out = alfa.process(mat)
    except Exception as exc:
        controls.set_status(f"Alfa error: {exc}")
        return

    controls.set_status("Running Beta...")
    controls.set_progress(0.10, "Beta")

    try:
        _beta_out = beta.process(mat)
    except Exception as exc:
        controls.set_status(f"Beta error: {exc}")
        return

    controls.set_status("Running Gama (sequencer)...")
    controls.set_progress(0.15, "Gama")

    def _progress_cb(step, total):
        frac = 0.15 + 0.80 * min(step / max(total, 1), 1.0)
        controls.set_progress(frac, f"Gama {step}/{total}")

    try:
        _events = generate(
            _alfa_out,
            _beta_out,
            horizon=hp["horizon"],
            gamma=hp["gamma"],
            lam=hp["lam"],
            omega_nuc=hp["omega_nuc"],
            omega_per=hp["omega_per"],
            beam_k=hp["beam_k"],
            callback=_progress_cb,
        )
    except Exception as exc:
        controls.set_status(f"Gama error: {exc}")
        return

    # Update views
    controls.update_info(
        tonic=NOTE_NAMES[_alfa_out.T],
        mode=_alfa_out.modo.upper(),
        ts=_beta_out.C,
        n_events=len(_events),
    )
    piano_roll.draw(_events, _beta_out.cap, _alfa_out.scale, _alfa_out.T)
    score_view.draw(_events, _beta_out.cap)
    controls.set_progress(1.0, "Done")
    controls.set_status(f"Generated {len(_events)} events.")


def _on_play(sender=None, app_data=None, user_data=None):
    global _wav_file
    if not _events:
        controls.set_status("Nothing to play – generate first.")
        return

    hp = controls.get_hyperparams()
    if _wav_file is None:
        controls.set_status("Rendering WAV...")
        _wav_file = audio.events_to_wav(
            _events, _OUTPUT_DIR / "preview.wav", bpm=hp["bpm"],
        )
    controls.set_status("Playing...")
    audio.play_wav(_wav_file)


def _on_stop(sender=None, app_data=None, user_data=None):
    audio.stop()
    controls.set_status("Stopped.")


def _on_export_midi(sender=None, app_data=None, user_data=None):
    global _midi_file
    if not _events or _beta_out is None:
        controls.set_status("Nothing to export – generate first.")
        return
    hp = controls.get_hyperparams()
    mid = audio.events_to_midi(_events, bpm=hp["bpm"], ts_str=_beta_out.C)
    _midi_file = audio.save_midi(mid, _OUTPUT_DIR / "output.mid")
    controls.set_status(f"MIDI saved → {_midi_file}")


def _on_export_wav(sender=None, app_data=None, user_data=None):
    global _wav_file
    if not _events:
        controls.set_status("Nothing to export – generate first.")
        return
    hp = controls.get_hyperparams()
    _wav_file = audio.events_to_wav(
        _events, _OUTPUT_DIR / "output.wav", bpm=hp["bpm"],
    )
    controls.set_status(f"WAV saved → {_wav_file}")


# ── Application entry point ────────────────────────────────────────

def run() -> None:
    """Launch the Dear PyGui application."""
    dpg.create_context()
    dpg.create_viewport(title="Método Murbach – Algorithmic Composer",
                        width=1280, height=800)

    # ── Theme ──
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 10, 10)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 4)
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (25, 25, 30, 255))
    dpg.bind_theme(global_theme)

    # ── Main window ──
    with dpg.window(tag="__main_win"):
        dpg.add_text("Metodo Murbach - Composicao Algoritmica Deterministica",
                      color=(140, 180, 255))
        dpg.add_separator()
        dpg.add_spacer(height=6)

        with dpg.group(horizontal=True):
            # ── LEFT column: matrix + controls ──
            with dpg.child_window(width=420, height=-1, border=True, tag="__left_col"):
                dpg.add_text("Seed Matrix", color=(200, 200, 255))
                dpg.add_spacer(height=4)
                matrix_editor.create("__left_col")
                dpg.add_spacer(height=10)
                dpg.add_separator()
                dpg.add_spacer(height=6)
                controls.create(
                    "__left_col",
                    on_generate=_on_generate,
                    on_play=_on_play,
                    on_stop=_on_stop,
                    on_export_midi=_on_export_midi,
                    on_export_wav=_on_export_wav,
                )

            dpg.add_spacer(width=8)

            # ── RIGHT column: piano roll + score ──
            with dpg.child_window(width=-1, height=-1, border=True, tag="__right_col"):
                dpg.add_text("Piano Roll", color=(200, 200, 255))
                piano_roll.create("__right_col", width=780, height=420)

                dpg.add_spacer(height=10)
                dpg.add_separator()
                dpg.add_spacer(height=4)
                dpg.add_text("Score", color=(200, 200, 255))
                score_view.create("__right_col")

    dpg.set_primary_window("__main_win", True)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()
