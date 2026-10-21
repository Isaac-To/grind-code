"""Reference solution — 695. Max Area of Island.

Approach: flood fill with an explicit stack (iterative DFS). For every land
cell not yet visited, flood its whole component, counting cells, and keep
the best count seen.

Invariant: `visited` always separates fully-counted components from
untouched ones, so each land cell is counted exactly once across all floods.

Complexity: O(m*n) time — each cell pushed at most once; O(m*n) space in the
worst case (one giant island fills the visited set and the stack).
"""
from __future__ import annotations


class Solution:
    def maxAreaOfIsland(self, grid: list[list[int]]) -> int:
        rows, cols = len(grid), len(grid[0])
        best = 0
        for r in range(rows):
            for c in range(cols):
                if grid[r][c] != 1:
                    continue          # water, or part of an island already counted
                area = 0
                stack = [(r, c)]     # iterative DFS avoids recursion limits
                grid[r][c] = 0       # mark on push so a cell enters the stack once
                while stack:
                    x, y = stack.pop()
                    area += 1
                    for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                        if 0 <= nx < rows and 0 <= ny < cols and grid[nx][ny] == 1:
                            grid[nx][ny] = 0   # sink now, not on pop
                            stack.append((nx, ny))
                best = max(best, area)
        return best
