"""Shared test fixtures."""

import pytest

MATRIX_3x3 = [
    [2, 7, 1],
    [5, 3, 8],
    [4, 6, 9],
]

MATRIX_4x4 = [
    [3, 1, 4, 1],
    [5, 9, 2, 6],
    [5, 3, 5, 8],
    [9, 7, 9, 3],
]

IDENTITY_3x3 = [
    [1, 0, 0],
    [0, 1, 0],
    [0, 0, 1],
]

SINGULAR_3x3 = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9],
]
