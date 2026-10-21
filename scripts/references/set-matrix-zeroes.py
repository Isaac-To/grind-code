"""Reference solution — 73. Set Matrix Zeroes.

Approach: the O(1)-space trick — use the matrix's own first row and first
column as the marker arrays. First record two flags (row0_has_zero,
col0_has_zero) saying whether the first row / first column themselves need
zeroing. Then, scanning the interior (i >= 1, j >= 1), write a 0 into
matrix[0][j] / matrix[i][0] whenever a zero is found. In a second phase,
sweep the interior again and zero any cell whose row or column marker is 0.
Finally apply the two saved flags to the first row and column.

Invariant: after the marking pass, matrix[0][j] == 0 means "column j must be
zeroed" and matrix[i][0] == 0 means "row i must be zeroed", for all i, j >= 1.
The two flags carry the information about row 0 / column 0 separately because
the cell matrix[0][0] can only encode one of them. Marker cells are never
consumed before the interior sweep, so markers cannot cascade (a marker zero
is never mistaken for an original zero during marking, since marking only
reads the interior).

Complexity: O(m*n) time — two full sweeps plus two boundary sweeps;
O(1) extra space.
"""
from __future__ import annotations


class Solution:
    def setZeroes(self, matrix: list[list[int]]) -> None:
        rows, cols = len(matrix), len(matrix[0])

        # Does the first row / first column contain a zero of its own?
        row0_has_zero = any(matrix[0][j] == 0 for j in range(cols))
        col0_has_zero = any(matrix[i][0] == 0 for i in range(rows))

        # Marking pass: interior zeros stamp their row/column markers in
        # row 0 and column 0.
        for i in range(1, rows):
            for j in range(1, cols):
                if matrix[i][j] == 0:
                    matrix[i][0] = 0   # mark: row i must be zeroed
                    matrix[0][j] = 0   # mark: column j must be zeroed

        # Clearing pass: interior cell dies if its row or column is marked.
        for i in range(1, rows):
            for j in range(1, cols):
                if matrix[i][0] == 0 or matrix[0][j] == 0:
                    matrix[i][j] = 0

        # Finally apply the saved flags to the border itself.
        if row0_has_zero:
            for j in range(cols):
                matrix[0][j] = 0
        if col0_has_zero:
            for i in range(rows):
                matrix[i][0] = 0
