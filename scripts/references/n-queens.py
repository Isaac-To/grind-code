"""Reference solution — 51. N-Queens.

Approach: place one queen per row (so no two queens can ever share a row),
scanning rows top to bottom and backtracking on dead ends. For each
candidate column we test three attack lines: the column, and the two
45°/135° diagonals. Two queens at (r1, c1) and (r2, c2) share a diagonal
iff r1 - c1 == r2 - c2 (the "\" direction) or r1 + c1 == r2 + c2 (the "/"
direction) — so three integer sets answer every safety check in O(1); no
board rescanning is ever needed.

Invariant: after placing k queens in rows 0..k-1, no two of them attack
each other (each was placed only on a still-free column/diagonal), and the
loop tries every safe column of row k. Hence if a placement exists, the
search finds one; if row n is reached, `cols` describes a full valid board.

Note on output shape: the canonical LeetCode problem returns *all* distinct
boards; this bank's grader instead accepts any single valid board, so we
return the first solution found (rendered as n strings, 'Q' at the queen's
column, '.' elsewhere). Collecting every solution instead of returning on
the first would give the classic all-boards variant.

Complexity: roughly O(n!) worst case (heavily pruned by the three sets);
O(n) extra space for the sets and the recursion stack.
"""
from __future__ import annotations


class Solution:
    def solveNQueens(self, n: int) -> list[list[str]]:
        cols: list[int] = []            # cols[r] = column of the queen in row r
        used_cols: set[int] = set()     # occupied columns
        used_diag: set[int] = set()     # occupied "\" diagonals (key r - c)
        used_anti: set[int] = set()     # occupied "/" diagonals (key r + c)

        def dfs(row: int) -> bool:
            if row == n:
                return True             # all n rows filled — a valid board
            for col in range(n):
                if col in used_cols:
                    continue            # another queen already holds this column
                if row - col in used_diag or row + col in used_anti:
                    continue            # diagonal attack — skip this square
                # Place the queen on (row, col).
                cols.append(col)
                used_cols.add(col)
                used_diag.add(row - col)
                used_anti.add(row + col)
                if dfs(row + 1):        # extend downward; stop at first success
                    return True
                # Remove the queen (backtrack) and try the next column.
                cols.pop()
                used_cols.remove(col)
                used_diag.remove(row - col)
                used_anti.remove(row + col)
            return False                # no safe column — backtrack a row

        dfs(0)
        # Render: each row r is all dots except a 'Q' at column cols[r].
        return ["." * c + "Q" + "." * (n - c - 1) for c in cols]
