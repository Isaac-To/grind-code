"""Reference solution — 329. Longest Increasing Path in a Matrix.

Approach: memoized depth-first search from every cell. Because moves must
strictly increase the value, the move graph is a DAG — no path can revisit
a cell — so the longest increasing path starting at a cell is a pure
function of that cell, cacheable forever (memoization, not visited-marks).

len(cell) = 1 + max(len(neighbour) for each strictly greater neighbour),
or 1 if no neighbour is larger.

Invariant: once memo[r][c] is set it never changes, and it equals the
longest strictly-increasing path starting at (r, c). The recursion only
steps to strictly larger values, so recursion depth is bounded by the
number of distinct values along a chain — termination is guaranteed.

Why it works: any increasing path through (r, c) continues into one of the
strictly greater neighbours; the best continuation is independent of how
we arrived (no revisits possible), so subproblems compose.

The answer is the max over all starting cells.

Complexity: O(m*n) time — each cell's DFS is computed once, each cell has
at most 4 out-edges; O(m*n) space for the memo (plus recursion stack).
"""
from __future__ import annotations


class Solution:
    def longestIncreasingPath(self, matrix: list[list[int]]) -> int:
        rows, cols = len(matrix), len(matrix[0])
        memo = [[0] * cols for _ in range(rows)]   # 0 = not computed yet

        def path_len(r: int, c: int) -> int:
            if memo[r][c]:                          # already solved exactly
                return memo[r][c]
            best = 1                                # the cell by itself
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                # strictly greater -> this is a DAG edge, no cycles
                if 0 <= nr < rows and 0 <= nc < cols and matrix[nr][nc] > matrix[r][c]:
                    best = max(best, 1 + path_len(nr, nc))
            memo[r][c] = best
            return best

        return max(path_len(r, c) for r in range(rows) for c in range(cols))
