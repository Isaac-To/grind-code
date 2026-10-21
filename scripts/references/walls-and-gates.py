"""Reference solution — 286. Walls and Gates.

Approach: multi-source BFS. All gates are seeded into the queue at
distance 0, then the BFS wavefront expands one step at a time. Because
BFS explores cells in order of distance, the first time the wavefront
reaches an empty room it does so along a shortest path from the *nearest*
gate, so we write the distance immediately and never revisit.

Invariant: every cell in the queue has its final distance filled in
`rooms`, and the wavefront only touches INF cells — anything smaller is
already solved optimally. Unreachable rooms stay INF, as required.

Complexity: O(m*n) time — each cell is enqueued at most once; O(m*n)
queue space in the worst case.
"""
from __future__ import annotations

from collections import deque

INF = 2147483647


class Solution:
    def wallsAndGates(self, rooms: list[list[int]]) -> None:
        rows, cols = len(rooms), len(rooms[0])
        queue = deque()
        for r in range(rows):
            for c in range(cols):
                if rooms[r][c] == 0:        # seed every gate at distance 0
                    queue.append((r, c))
        while queue:
            x, y = queue.popleft()
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if 0 <= nx < rows and 0 <= ny < cols and rooms[nx][ny] == INF:
                    rooms[nx][ny] = rooms[x][y] + 1   # one step farther than parent
                    queue.append((nx, ny))
