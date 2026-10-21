"""Reference solution — 200. Number of Islands.

Approach: flood fill. Scan every cell; when we meet an unvisited land cell
we have found a new island, so we run a BFS that "sinks" the whole island
(marking its cells as water) and bump the counter. Sinking guarantees each
island is counted exactly once, no matter how many of its cells the scan
touches later.

Invariant: after the scan finishes a cell, every island cell at or before
the current scan position has been fully sunk. Hence the counter equals the
number of distinct connected land components.

Complexity: O(m*n) time — each cell is enqueued at most once because we
mark it visited on enqueue, not on dequeue; O(min(m, n)) BFS queue space.
"""
from __future__ import annotations

from collections import deque


class Solution:
    def numIslands(self, grid: list[list[str]]) -> int:
        rows, cols = len(grid), len(grid[0])
        count = 0
        for r in range(rows):          # sweep the grid top-to-bottom, left-to-right
            for c in range(cols):
                if grid[r][c] != "1":  # water or already-sunk land -> skip
                    continue
                count += 1             # first cell of a brand-new island
                queue = deque([(r, c)])
                grid[r][c] = "0"        # sink immediately so it is never re-queued
                while queue:
                    x, y = queue.popleft()
                    # explore the four orthogonal neighbours
                    for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                        if 0 <= nx < rows and 0 <= ny < cols and grid[nx][ny] == "1":
                            grid[nx][ny] = "0"   # mark on enqueue: no duplicates
                            queue.append((nx, ny))
        return count
