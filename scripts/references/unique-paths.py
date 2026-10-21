"""Reference solution — 62. Unique Paths.

Approach: dynamic programming over the grid. The robot can only move right
or down, so the number of ways to reach cell (r, c) is exactly
    paths(r, c) = paths(r-1, c) + paths(r, c-1)
because the last move into (r, c) was either a down-step from above or a
right-step from the left. Every cell in the top row and the left column has
exactly one path (a straight line of single-direction moves).

Invariant: after processing row r, dp[c] holds the number of unique paths
from (0, 0) to (r, c). We roll the 2-D table into a single 1-D row:
dp[c] on the right side of the assignment below is still "the row above"
(paths(r-1, c)), while dp[c-1] has just been updated to "this row, left
neighbour" (paths(r, c-1)).

Why it works: each path to (r, c) ends with exactly one of the two allowed
last moves, and the two sets of paths are disjoint — so their counts add.

Complexity: O(m*n) time, O(n) space for the rolled row.
"""
from __future__ import annotations


class Solution:
    def uniquePaths(self, m: int, n: int) -> int:
        # One row suffices: first row of the grid is all 1s.
        dp = [1] * n
        for _ in range(1, m):          # each pass fills in the next row
            for c in range(1, n):      # column 0 stays 1 (straight-down path)
                dp[c] += dp[c - 1]      # above (old dp[c]) + left (new dp[c-1])
        return dp[-1]
