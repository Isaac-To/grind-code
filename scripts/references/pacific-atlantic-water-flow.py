"""Reference solution — 417. Pacific Atlantic Water Flow.

Approach: think backwards. Instead of asking "where does water from each
cell flow?", start from the ocean borders and climb *uphill* (move to a
neighbour with height >= current). Two BFS runs collect the cells that can
reach each ocean; the answer is the intersection.

Invariant: `pacific` (resp. `atlantic`) ends up containing exactly the
cells with a non-increasing path to that ocean, because climbing in
reverse turns every downstream edge into an upstream one.

Complexity: O(m*n) time — each ocean BFS visits each cell once;
O(m*n) space for the two visited sets and queues.
"""
from __future__ import annotations

from collections import deque


class Solution:
    def pacificAtlantic(self, heights: list[list[int]]) -> list[list[int]]:
        rows, cols = len(heights), len(heights[0])

        def bfs(ocean_seeds: set[tuple[int, int]]) -> set[tuple[int, int]]:
            """Reverse-climb from `ocean_seeds`; return all reachable cells."""
            visited = set(ocean_seeds)
            queue = deque(ocean_seeds)
            while queue:
                x, y = queue.popleft()
                # step uphill: neighbour must be at least as tall to flow down to us
                for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    if (0 <= nx < rows and 0 <= ny < cols
                            and (nx, ny) not in visited
                            and heights[nx][ny] >= heights[x][y]):
                        visited.add((nx, ny))
                        queue.append((nx, ny))
            return visited

        # Pacific touches the top row and left column; Atlantic the bottom and right.
        pacific_seeds = {(0, c) for c in range(cols)} | {(r, 0) for r in range(rows)}
        atlantic_seeds = {(rows - 1, c) for c in range(cols)} | {(r, cols - 1) for r in range(rows)}

        # Row-major order over the intersection keeps the output deterministic.
        return [[r, c] for r in range(rows) for c in range(cols)
                if (r, c) in bfs(pacific_seeds) and (r, c) in bfs(atlantic_seeds)]
