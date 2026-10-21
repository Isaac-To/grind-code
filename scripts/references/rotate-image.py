"""Reference solution — 48. Rotate Image.

Approach: rotate an n x n matrix 90 degrees clockwise in two reflections.
  1. Transpose: mirror every element across the main diagonal
     (swap matrix[i][j] with matrix[j][i] for j > i).
  2. Reverse each row: mirror every row left-to-right.

Why it works: the two reflections compose into a quarter turn.
A cell (i, j) first moves to (j, i) under the transpose, then reversing
its row takes column i to column n-1-i, so (j, i) -> (j, n-1-i).
Overall (i, j) -> (j, n-1-i), which is exactly the clockwise-90 map:
row index becomes column index, and the column index is flipped.

Invariant: every swap touches only cells that have not yet been reflected,
so each element is moved exactly once per reflection — pure in-place,
O(1) extra space, no second matrix.

Complexity: O(n^2) time — each element is visited a constant number of
times; O(1) extra space — only swap temporaries.
"""
from __future__ import annotations


class Solution:
    def rotate(self, matrix: list[list[int]]) -> None:
        """Rotate the square matrix 90 degrees clockwise in-place."""
        n = len(matrix)

        # Pass 1: transpose — swap across the main diagonal.
        # Only visit j > i so each pair is swapped exactly once
        # (visiting both triangles would swap everything back!).
        for i in range(n):
            for j in range(i + 1, n):
                matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]

        # Pass 2: reverse each row, turning the transpose into a clockwise turn.
        for row in matrix:
            row.reverse()
