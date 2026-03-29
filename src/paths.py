"""
Frozen-aware path resolution for PyInstaller bundles.

When running as a PyInstaller one-dir or one-file bundle, ``sys._MEIPASS``
points to the temporary extraction folder. This module exposes a single
``ROOT`` that always resolves to the project root regardless of context.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _resolve_root() -> Path:
    if getattr(sys, "frozen", False):
        # Running inside a PyInstaller bundle
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    # Normal execution: <project>/src/paths.py -> <project>
    return Path(__file__).resolve().parent.parent


def _resolve_output() -> Path:
    if getattr(sys, "frozen", False):
        # Write outputs next to the executable, not inside _internal/
        return Path(sys.executable).resolve().parent / "output"
    return Path(__file__).resolve().parent.parent / "output"


ROOT = _resolve_root()
SOUNDFONTS_DIR = ROOT / "soundfonts"
OUTPUT_DIR = _resolve_output()
