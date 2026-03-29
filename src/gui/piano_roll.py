"""
Piano Roll visualisation – draws note events on a DPG draw-list canvas.
"""

from __future__ import annotations

from fractions import Fraction

import dearpygui.dearpygui as dpg

from ..murbach.config import NOTE_NAMES
from ..murbach.types import Event

# Colours per scale degree (index 0–11 → RGBA)
_DEGREE_COLORS = [
    (230, 80, 80, 200),    # C  – red
    (200, 100, 60, 200),   # C#
    (240, 180, 50, 200),   # D  – gold
    (180, 200, 60, 200),   # D#
    (80, 200, 80, 200),    # E  – green
    (60, 180, 160, 200),   # F  – teal
    (60, 140, 220, 200),   # F#
    (80, 100, 230, 200),   # G  – blue
    (130, 80, 220, 200),   # G#
    (180, 60, 200, 200),   # A  – purple
    (220, 60, 160, 200),   # A#
    (220, 80, 120, 200),   # B  – pink
]

_GRID_COLOR = (60, 60, 60, 120)
_BAR_LINE_COLOR = (180, 180, 180, 200)
_BG_COLOR = (30, 30, 35, 255)

_canvas_tag: int | str | None = None
_draw_layer: int | str | None = None

# Layout constants
NOTE_H = 16      # pixel height per semitone row
TIME_SCALE = 300  # pixels per whole note
PADDING_LEFT = 50
PADDING_TOP = 10


def create(parent: int | str, width: int = 780, height: int = 420) -> None:
    """Add the piano-roll draw-list to *parent*."""
    global _canvas_tag
    _canvas_tag = dpg.add_drawlist(
        width=width, height=height, parent=parent,
        tag="__pr_canvas",
    )


def draw(
    events: list[Event],
    cap: Fraction,
    scale: list[int],
    tonic: int,
) -> None:
    """Clear and redraw the piano roll for the given events."""
    dpg.delete_item("__pr_canvas", children_only=True)

    if not events:
        return

    # Determine MIDI range for Y axis
    midi_notes = [e.midi_note for e in events]
    lo = min(midi_notes) - 1
    hi = max(midi_notes) + 2
    nrows = hi - lo

    canvas_w = dpg.get_item_width("__pr_canvas")
    canvas_h = dpg.get_item_height("__pr_canvas")

    # Compute total time for X scaling
    total_dur = sum(float(e.duration) for e in events)
    if total_dur == 0:
        return
    ts = (canvas_w - PADDING_LEFT - 20) / total_dur  # pixels per whole-note-unit

    row_h = max(6, (canvas_h - PADDING_TOP - 10) / nrows)

    def y_of(midi: int) -> float:
        return PADDING_TOP + (hi - midi - 1) * row_h

    def x_of(time: float) -> float:
        return PADDING_LEFT + time * ts

    # ── Background grid ──
    for midi in range(lo, hi + 1):
        y = y_of(midi)
        pc = midi % 12
        # Highlight scale tones
        if pc in scale:
            dpg.draw_rectangle(
                pmin=(PADDING_LEFT, y),
                pmax=(canvas_w - 10, y + row_h),
                fill=(45, 45, 50, 255),
            parent="__pr_canvas",
        )
        # Pitch label
        name = NOTE_NAMES[pc] + str(midi // 12 - 1)
        dpg.draw_text(
            pos=(4, y + 1), text=name, size=11,
            color=(160, 160, 160, 255),
            parent="__pr_canvas",
        )
        # Horizontal grid line
        dpg.draw_line(
            p1=(PADDING_LEFT, y), p2=(canvas_w - 10, y),
            color=_GRID_COLOR,
            parent="__pr_canvas",
        )

    # ── Bar lines ──
    cap_f = float(cap)
    if cap_f > 0:
        bar_x = 0.0
        while bar_x <= total_dur + cap_f:
            px = x_of(bar_x)
            dpg.draw_line(
                p1=(px, PADDING_TOP), p2=(px, PADDING_TOP + nrows * row_h),
                color=_BAR_LINE_COLOR, thickness=1,
                parent="__pr_canvas",
            )
            bar_x += cap_f

    # ── Note rectangles ──
    t = 0.0
    for ev in events:
        x1 = x_of(t)
        x2 = x_of(t + float(ev.duration))
        y1 = y_of(ev.midi_note)
        color = _DEGREE_COLORS[ev.pitch % 12]
        dpg.draw_rectangle(
            pmin=(x1 + 1, y1 + 1),
            pmax=(x2 - 1, y1 + row_h - 1),
            fill=color,
            color=(255, 255, 255, 80),
            rounding=3,
            parent="__pr_canvas",
        )
        # Note label inside
        if x2 - x1 > 20:
            dpg.draw_text(
                pos=(x1 + 3, y1 + 2),
                text=NOTE_NAMES[ev.pitch],
                size=10,
                color=(255, 255, 255, 220),
                parent="__pr_canvas",
            )
        t += float(ev.duration)
