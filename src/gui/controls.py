"""
Controls panel – buttons, sliders, info readout.
"""

from __future__ import annotations

import dearpygui.dearpygui as dpg

from ..murbach.config import (
    BEAM_K,
    DEFAULT_BPM,
    GAMMA,
    HORIZON,
    LAMBDA,
    OMEGA_NUC,
    OMEGA_PER,
)


def create(
    parent: int | str,
    on_generate=None,
    on_play=None,
    on_stop=None,
    on_export_midi=None,
    on_export_wav=None,
) -> None:
    """Build controls inside *parent*."""

    with dpg.group(parent=parent):
        # ── Action buttons ──
        dpg.add_text("Actions", color=(200, 200, 255))
        with dpg.group(horizontal=True):
            dpg.add_button(label="Generate", callback=on_generate,
                           width=100, tag="__ctrl_gen")
            dpg.add_button(label="Play", callback=on_play,
                           width=70, tag="__ctrl_play")
            dpg.add_button(label="Stop", callback=on_stop,
                           width=70, tag="__ctrl_stop")
        with dpg.group(horizontal=True):
            dpg.add_button(label="Export MIDI", callback=on_export_midi,
                           width=100, tag="__ctrl_midi")
            dpg.add_button(label="Export WAV", callback=on_export_wav,
                           width=100, tag="__ctrl_wav")

        dpg.add_spacer(height=10)
        dpg.add_separator()
        dpg.add_spacer(height=6)

        # ── Info panel ──
        dpg.add_text("Info", color=(200, 200, 255))
        dpg.add_text("Tonic: –", tag="__ctrl_info_tonic")
        dpg.add_text("Mode: –", tag="__ctrl_info_mode")
        dpg.add_text("Time sig: –", tag="__ctrl_info_ts")
        dpg.add_text("Events: –", tag="__ctrl_info_events")
        dpg.add_text("", tag="__ctrl_info_status")

        dpg.add_spacer(height=10)
        dpg.add_separator()
        dpg.add_spacer(height=6)

        # ── Hyperparameters ──
        dpg.add_text("Hyperparameters", color=(200, 200, 255))
        dpg.add_slider_int(label="BPM", default_value=DEFAULT_BPM,
                           min_value=40, max_value=240, width=200,
                           tag="__ctrl_bpm")
        dpg.add_slider_int(label="Horizon (h)", default_value=HORIZON,
                           min_value=0, max_value=8, width=200,
                           tag="__ctrl_horizon")
        dpg.add_slider_float(label="Gamma", default_value=GAMMA,
                             min_value=0.0, max_value=1.0, width=200,
                             format="%.2f", tag="__ctrl_gamma")
        dpg.add_slider_float(label="Lambda", default_value=LAMBDA,
                             min_value=0.0, max_value=1.0, width=200,
                             format="%.2f", tag="__ctrl_lambda")
        dpg.add_slider_float(label="w_nuc", default_value=OMEGA_NUC,
                             min_value=0.0, max_value=10.0, width=200,
                             format="%.1f", tag="__ctrl_omega_nuc")
        dpg.add_slider_float(label="w_per", default_value=OMEGA_PER,
                             min_value=0.0, max_value=10.0, width=200,
                             format="%.1f", tag="__ctrl_omega_per")
        dpg.add_slider_int(label="Beam K", default_value=BEAM_K,
                           min_value=1, max_value=20, width=200,
                           tag="__ctrl_beam_k")

        dpg.add_spacer(height=10)
        dpg.add_progress_bar(default_value=0.0, tag="__ctrl_progress",
                             width=260, overlay="Ready")


def get_hyperparams() -> dict:
    return {
        "bpm": dpg.get_value("__ctrl_bpm"),
        "horizon": dpg.get_value("__ctrl_horizon"),
        "gamma": dpg.get_value("__ctrl_gamma"),
        "lam": dpg.get_value("__ctrl_lambda"),
        "omega_nuc": dpg.get_value("__ctrl_omega_nuc"),
        "omega_per": dpg.get_value("__ctrl_omega_per"),
        "beam_k": dpg.get_value("__ctrl_beam_k"),
    }


def update_info(tonic: str, mode: str, ts: str, n_events: int) -> None:
    dpg.set_value("__ctrl_info_tonic", f"Tonic: {tonic}")
    dpg.set_value("__ctrl_info_mode", f"Mode: {mode}")
    dpg.set_value("__ctrl_info_ts", f"Time sig: {ts}")
    dpg.set_value("__ctrl_info_events", f"Events: {n_events}")


def set_status(text: str) -> None:
    dpg.set_value("__ctrl_info_status", text)


def set_progress(frac: float, overlay: str = "") -> None:
    dpg.set_value("__ctrl_progress", min(frac, 1.0))
    dpg.configure_item("__ctrl_progress", overlay=overlay or f"{int(frac*100)}%")
