"""Reference solution — 36. Valid Sudoku.

Approach: each digit must be unique within its row, its column, and its
3x3 sub-box. Track the digits seen so far in each of the 27 units with
hash sets; on seeing a digit already present in any of its three units,
the board is invalid. Cells holding '.' are skipped.

Invariant: when we process cell (r, c) with digit d, the sets contain
exactly the digits previously placed in row r, column c, and box
(r // 3, c // 3). So a hit means d clashes with an earlier cell in that
unit — checking every cell once is sufficient because a duplicate pair
is caught at its *second* occurrence.

Complexity: O(81) = O(1) time and space for the fixed 9x9 board.
"""
from __future__ import annotations


class Solution:
    def isValidSudoku(self, board: list[list[str]]) -> bool:
        rows = [set() for _ in range(9)]      # digits seen in each row
        cols = [set() for _ in range(9)]      # ... in each column
        boxes = [set() for _ in range(9)]    # ... in each 3x3 sub-box
        for r in range(9):
            for c in range(9):
                d = board[r][c]
                if d == ".":                  # empty cells impose no rule
                    continue
                b = (r // 3) * 3 + c // 3      # box index 0..8
                if d in rows[r] or d in cols[c] or d in boxes[b]:
                    return False              # duplicate within a unit
                rows[r].add(d)
                cols[c].add(d)
                boxes[b].add(d)
        return True                           # every unit stayed duplicate-free
