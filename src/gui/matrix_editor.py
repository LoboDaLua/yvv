"""
Matrix Editor widget – editable n×n integer grid for seed input.
Supports arbitrary square matrix sizes and CSV import/export.
"""

from __future__ import annotations

import csv
import os
import random
from pathlib import Path

import dearpygui.dearpygui as dpg

from ..paths import OUTPUT_DIR

# Pre-loaded example matrices
EXAMPLES = {
    "3×3 Basic": [
        [2, 7, 1],
        [5, 3, 8],
        [4, 6, 9],
    ],
    "3×3 Identity": [
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
    ],
    "4×4 Murbach": [
        [3, 1, 4, 1],
        [5, 9, 2, 6],
        [5, 3, 5, 8],
        [9, 7, 9, 3],
    ],
    "4×4 Fibonacci": [
        [1, 1, 2, 3],
        [5, 8, 13, 21],
        [34, 55, 89, 144],
        [233, 377, 610, 987],
    ],
    "5×5 Primes": [
        [2, 3, 5, 7, 11],
        [13, 17, 19, 23, 29],
        [31, 37, 41, 43, 47],
        [53, 59, 61, 67, 71],
        [73, 79, 83, 89, 97],
    ],
}

_cell_tags: list[list[int | str]] = []
_current_size = 4
_grid_parent: int | str | None = None
_status_callback = None


def create(parent: int | str, on_size_change=None, on_status=None) -> None:
    """Build the matrix editor inside *parent*."""
    global _grid_parent, _status_callback
    _grid_parent = parent
    _status_callback = on_status

    with dpg.group(parent=parent, tag="__me_root"):
        with dpg.group(horizontal=True):
            dpg.add_text("Size:")
            dpg.add_input_int(
                default_value=4,
                min_value=2,
                min_clamped=True,
                max_value=64,
                max_clamped=True,
                width=60,
                step=1,
                tag="__me_size",
                callback=lambda s, a, u: _rebuild(a),
            )
        with dpg.group(horizontal=True):
            dpg.add_text("Example:")
            dpg.add_combo(
                items=list(EXAMPLES.keys()),
                default_value="4×4 Murbach",
                width=180,
                tag="__me_example",
                callback=lambda s, a, u: _load_example(a),
            )
        with dpg.group(horizontal=True):
            dpg.add_button(label="Import CSV", callback=_on_import_csv,
                           width=100, tag="__me_import_csv")
            dpg.add_button(label="Export CSV", callback=_on_export_csv,
                           width=100, tag="__me_export_csv")
            dpg.add_button(label="Randomize", callback=_on_randomize,
                           width=100, tag="__me_randomize")

        # File dialogs (hidden until invoked)
        with dpg.file_dialog(
            directory_selector=False,
            show=False,
            callback=_import_csv_callback,
            cancel_callback=lambda s, a: None,
            width=600,
            height=400,
            tag="__me_import_dialog",
        ):
            dpg.add_file_extension(".csv", color=(0, 255, 0, 255))

        with dpg.file_dialog(
            directory_selector=False,
            show=False,
            callback=_export_csv_callback,
            cancel_callback=lambda s, a: None,
            width=600,
            height=400,
            tag="__me_export_dialog",
            default_filename="matrix.csv",
        ):
            dpg.add_file_extension(".csv", color=(0, 255, 0, 255))

        dpg.add_spacer(height=6)
        dpg.add_child_window(
            tag="__me_grid_scroll",
            horizontal_scrollbar=True,
            height=260,
            border=False,
        )
        dpg.add_group(tag="__me_grid_area", parent="__me_grid_scroll")

    _rebuild(4)
    _load_example("4×4 Murbach")


def _rebuild(n: int) -> None:
    global _cell_tags, _current_size
    n = max(2, min(n, 64))
    _current_size = n

    # Delete old cell tags explicitly before clearing container
    for row in _cell_tags:
        for tag in row:
            if dpg.does_item_exist(tag):
                dpg.delete_item(tag)
    _cell_tags = []

    dpg.delete_item("__me_grid_area", children_only=True)

    for i in range(n):
        row_tags = []
        with dpg.group(horizontal=True, parent="__me_grid_area"):
            for j in range(n):
                tag = f"__me_c_{i}_{j}"
                if dpg.does_item_exist(tag):
                    dpg.delete_item(tag)
                dpg.add_input_int(
                    default_value=0, width=48, step=0,
                    tag=tag,
                )
                row_tags.append(tag)
        _cell_tags.append(row_tags)


def _load_example(name: str) -> None:
    mat = EXAMPLES.get(name)
    if mat is None:
        return
    n = len(mat)
    if n != _current_size:
        _rebuild(n)
        dpg.set_value("__me_size", n)
    set_matrix(mat)


def get_matrix() -> list[list[int]]:
    """Read the current grid values and return an n×n list of ints."""
    n = _current_size
    return [
        [dpg.get_value(_cell_tags[i][j]) for j in range(n)]
        for i in range(n)
    ]


def set_matrix(mat: list[list[int]]) -> None:
    """Write values into the grid."""
    n = min(len(mat), _current_size)
    for i in range(n):
        for j in range(min(len(mat[i]), _current_size)):
            dpg.set_value(_cell_tags[i][j], mat[i][j])


def load_matrix_from_csv(path: str | Path) -> list[list[int]]:
    """Read a CSV file and return the matrix as a list of int lists."""
    mat: list[list[int]] = []
    with open(path, newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            mat.append([int(cell) for cell in row])
    return mat


def save_matrix_to_csv(mat: list[list[int]], path: str | Path) -> Path:
    """Write the matrix to a CSV file and return the path."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(mat)
    return p


def _on_randomize(sender=None, app_data=None, user_data=None) -> None:
    """Fill the current matrix with random integers in [0, 100]."""
    n = _current_size
    for i in range(n):
        for j in range(n):
            dpg.set_value(_cell_tags[i][j], random.randint(0, 100))
    _set_status(f"Randomized {n}×{n} matrix.")


def _set_status(text: str) -> None:
    if _status_callback is not None:
        _status_callback(text)


def _on_import_csv(sender=None, app_data=None, user_data=None) -> None:
    dpg.show_item("__me_import_dialog")


def _on_export_csv(sender=None, app_data=None, user_data=None) -> None:
    dpg.show_item("__me_export_dialog")


def _import_csv_callback(sender, app_data, user_data=None) -> None:
    selections = app_data.get("selections", {})
    if not selections:
        return
    filepath = list(selections.values())[0]
    try:
        mat = load_matrix_from_csv(filepath)
        if not mat:
            _set_status("CSV file is empty.")
            return
        n = len(mat)
        if n != _current_size:
            _rebuild(n)
            dpg.set_value("__me_size", n)
        set_matrix(mat)
        _set_status(f"Imported {n}×{len(mat[0])} matrix from CSV.")
    except Exception as exc:
        _set_status(f"CSV import error: {exc}")


def _export_csv_callback(sender, app_data, user_data=None) -> None:
    file_path_name = app_data.get("file_path_name", "")
    if not file_path_name:
        return
    try:
        mat = get_matrix()
        p = save_matrix_to_csv(mat, file_path_name)
        _set_status(f"Matrix exported → {p}")
    except Exception as exc:
        _set_status(f"CSV export error: {exc}")
