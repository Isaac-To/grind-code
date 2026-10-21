"""Reference solution — 54. Spiral Matrix.

Approach: walk the matrix layer by layer, keeping a shrinking rectangular
window [top, bottom] x [left, right]. Each layer is peeled in four moves:
across the top row, down the right column, back along the bottom row
(only if it is distinct from the top row), and up the left column (only if
it is distinct from the right column). After a full loop the window shrinks
by one on every side.

Invariant: at the start of each iteration, every element outside the window
has already been appended to the output, and the output preserves the spiral
order. The two "distinct row/column" guards are what keep a single leftover
row or column from being traversed twice (the classic m==1 or n==1 trap, and
the odd-center cases like 3x3 where the middle row is both top and bottom).

Complexity: O(m*n) time — each element is appended exactly once;
O(1) extra space besides the output list.
"""
from __future__ import annotations


class Solution:
    def spiralOrder(self, matrix: list[list[int]]) -> list[int]:
        out: list[int] = []
        top, bottom = 0, len(matrix) - 1        # inclusive row bounds
        left, right = 0, len(matrix[0]) - 1     # inclusive column bounds

        while top <= bottom and left <= right:
            # 1) top row, left -> right
            for col in range(left, right + 1):
                out.append(matrix[top][col])
            top += 1

            # 2) right column, top -> bottom
            for row in range(top, bottom + 1):
                out.append(matrix[row][right])
            right -= 1

            # 3) bottom row, right -> left (skip if top overtook bottom)
            if top <= bottom:
                for col in range(right, left - 1, -1):
                    out.append(matrix[bottom][col])
                bottom -= 1

            # 4) left column, bottom -> top (skip if right overtook left)
            if left <= right:
                for row in range(bottom, top - 1, -1):
                    out.append(matrix[row][left])
                left += 1

        return out
