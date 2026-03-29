# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Método Murbach.

Build commands:
    pyinstaller murbach.spec          # one-dir bundle (default)
    pyinstaller murbach.spec --clean  # clean rebuild
"""

import os
import sys
from pathlib import Path

block_cipher = None

ROOT = Path(SPECPATH)

a = Analysis(
    [str(ROOT / "src" / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        # Bundle soundfont files
        (str(ROOT / "soundfonts"), "soundfonts"),
    ],
    hiddenimports=[
        "src",
        "src.paths",
        "src.murbach",
        "src.murbach.alfa",
        "src.murbach.beta",
        "src.murbach.gama",
        "src.murbach.audio",
        "src.murbach.config",
        "src.murbach.types",
        "src.murbach.utils",
        "src.gui",
        "src.gui.app",
        "src.gui.controls",
        "src.gui.matrix_editor",
        "src.gui.piano_roll",
        "src.gui.score_view",
        "tinysoundfont",
        "tinysoundfont._tinysoundfont",
        "sounddevice",
        "soundfile",
        "numpy",
        "mido",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "tkinter"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MetodoMurbach",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,   # windowed application (no terminal)
    icon=None,        # add an .ico path here if you have one
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="MetodoMurbach",
)
