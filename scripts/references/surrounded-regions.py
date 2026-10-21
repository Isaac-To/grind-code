"""Reference solution — 130. Surrounded Regions.

Approach: capture by complement. Any 'O' connected to the board edge can
never be surrounded, so mark those cells as safe ('S') with a DFS along
the border, then sweep: remaining 'O's (fully enclosed) become 'X', and
safe cells are restored to 'O'.

Invariant: when the marking DFS finishes, a cell is 'S' iff it belongs to
a region touching the border — the only regions that escape capture.

Complexity: O(m*n) time — each cell is visited a constant number of
times; O(m*n) worst-case space for the recursion (long border snake).
"""
from __future__ import annotations


class Solution:
    def solve(self, board: list[list[str]]) -> None:
        """Modify board in-place; captured regions of 'O' become 'X'."""
        rows, cols = len(board), len(board[0])

        def mark_safe(r: int, c: int) -> None:
            """Flood-fill one border-connected 'O' region into 'S'."""
            if r < 0 or r >= rows or c < 0 or c >= cols or board[r][c] != "O":
                return                       # out of bounds, wall, or already handled
            board[r][c] = "S"                # temporary marker: survives capture
            mark_safe(r - 1, c)              # recurse into the four neighbours
            mark_safe(r + 1, c)
            mark_safe(r, c - 1)
            mark_safe(r, c + 1)

        # Only border cells can start an un-surroundable region.
        for c in range(cols):
            mark_safe(0, c)                  # top edge
            mark_safe(rows - 1, c)           # bottom edge
        for r in range(rows):
            mark_safe(r, 0)                  # left edge
            mark_safe(r, cols - 1)           # right edge

        # Sweep: leftover 'O's are enclosed -> capture; restore 'S' -> 'O'.
        for r in range(rows):
            for c in range(cols):
                if board[r][c] == "O":
                    board[r][c] = "X"        # enclosed region: captured
                elif board[r][c] == "S":
                    board[r][c] = "O"         # border-connected: keep it
