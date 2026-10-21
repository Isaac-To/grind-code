"""Reference solution — 79. Word Search.

Approach: try a DFS from every cell whose letter matches word[0]. The DFS
consumes one character per step and marks the current cell '#' so the path
cannot reuse it; the mark is restored on the way out (backtracking), so
other starting cells see a pristine board. If the word is consumed exactly
on the last character, we found a path.

Invariant: dfs(r, c, k) is True iff word[k:] can be traced starting at cell
(r, c) using each cell at most once among the currently marked path. The
board equals the input except for the cells on the active path stack, which
are restored before every return — the board is never permanently mutated.

Complexity: O(m * n * 3^L) time — L = len(word); each step after the first
has at most 3 unvisited neighbours (we came from the fourth). O(L) depth.
"""
from __future__ import annotations


class Solution:
    def exist(self, board: list[list[str]], word: str) -> bool:
        rows, cols = len(board), len(board[0])

        def dfs(r: int, c: int, k: int) -> bool:
            if board[r][c] != word[k]:
                return False  # this cell cannot supply the k-th character
            if k == len(word) - 1:
                return True  # last character matched — whole word traced
            board[r][c] = "#"  # burn the cell so the path cannot revisit it
            found = False
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and dfs(nr, nc, k + 1):
                    found = True
                    break  # one success is enough — stop searching
            board[r][c] = word[k]  # restore the letter (backtrack)
            return found

        return any(
            dfs(r, c, 0) for r in range(rows) for c in range(cols)
        )
