"""
Matrix Editor widget – editable n×n integer grid for seed input.
"""

from __future__ import annotations

import dearpygui.dearpygui as dpg

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


def create(parent: int | str, on_size_change=None) -> None:
    """Build the matrix editor inside *parent*."""
    global _grid_parent
    _grid_parent = parent

    with dpg.group(parent=parent, tag="__me_root"):
        with dpg.group(horizontal=True):
            dpg.add_text("Size:")
            dpg.add_combo(
                items=["3", "4", "5", "6", "7", "8"],
                default_value="4",
                width=60,
                tag="__me_size",
                callback=lambda s, a, u: _rebuild(int(a)),
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

        dpg.add_spacer(height=6)
        dpg.add_group(tag="__me_grid_area")

    _rebuild(4)
    _load_example("4×4 Murbach")


def _rebuild(n: int) -> None:
    global _cell_tags, _current_size
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
        dpg.set_value("__me_size", str(n))
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
        for j in range(n):
            dpg.set_value(_cell_tags[i][j], mat[i][j])
