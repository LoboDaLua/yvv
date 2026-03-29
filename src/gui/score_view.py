"""
Simplified score / event-list view.
"""

from __future__ import annotations

from fractions import Fraction

import dearpygui.dearpygui as dpg

from ..murbach.config import NOTE_NAMES
from ..murbach.types import Event

_DUR_SYMBOLS = {
    Fraction(1, 1): "\U0001D15D",     # 𝅝 whole
    Fraction(1, 2): "\U0001D15E",     # 𝅗𝅥 half
    Fraction(1, 4): "\U0001D15F",     # 𝅘𝅥 quarter
    Fraction(1, 8): "\U0001D160",     # 𝅘𝅥𝅮 eighth
}


def _dur_label(d: Fraction) -> str:
    return _DUR_SYMBOLS.get(d, str(d))


_text_tag: int | str | None = None


def create(parent: int | str) -> None:
    global _text_tag
    dpg.add_text("", tag="__sv_text", parent=parent, wrap=760)
    _text_tag = "__sv_text"


def draw(events: list[Event], cap: Fraction) -> None:
    """Render event list as a text-based score."""
    if not events:
        dpg.set_value("__sv_text", "(no events)")
        return

    parts: list[str] = []
    bar_acc = Fraction(0)
    bar_num = 1
    parts.append(f"[{bar_num}] ")

    for ev in events:
        name = NOTE_NAMES[ev.pitch]
        octave = ev.midi_note // 12 - 1
        dur_s = _dur_label(ev.duration)
        parts.append(f"{name}{octave}{dur_s} ")
        bar_acc += ev.duration
        if bar_acc >= cap:
            bar_acc = Fraction(0)
            bar_num += 1
            parts.append(f" | [{bar_num}] ")

    dpg.set_value("__sv_text", "".join(parts))
