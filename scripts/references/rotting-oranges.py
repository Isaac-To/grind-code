"""Reference solution — 994. Rotting Oranges.

Approach: multi-source BFS, one wavefront per minute. Start from every
rotten orange at minute 0; each BFS level spreads the rot one step in all
four directions. Fresh oranges that can never be reached (isolated by
empty cells) make the total fresh count nonzero at the end -> -1.

Invariant: after `minutes` loop iterations, every fresh orange within
`minutes` steps of some rotten orange has been rotted. Tracking
`fresh_left` while spreading gives the two possible endings for free.

Complexity: O(m*n) time — each cell enters the queue at most once;
O(m*n) space for the queue.
"""
from __future__ import annotations

from collections import deque


class Solution:
    def orangesRotting(self, grid: list[list[int]]) -> int:
        rows, cols = len(grid), len(grid[0])
        queue = deque()
        fresh = 0
        for r in range(rows):
            for c in range(cols):
                if grid[r][c] == 2:          # rotten: BFS source at minute 0
                    queue.append((r, c))
                elif grid[r][c] == 1:
                    fresh += 1               # count fresh oranges up front

        minutes = 0
        while queue and fresh > 0:            # no work left if nothing is fresh
            minutes += 1                     # this wavefront takes one minute
            for _ in range(len(queue)):      # process exactly one BFS level
                x, y = queue.popleft()
                for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    if 0 <= nx < rows and 0 <= ny < cols and grid[nx][ny] == 1:
                        grid[nx][ny] = 2     # rot it now so no neighbour double-counts
                        fresh -= 1
                        queue.append((nx, ny))

        return minutes if fresh == 0 else -1  # leftover fresh orange = unreachable
