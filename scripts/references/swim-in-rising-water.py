"""Reference solution — 778. Swim in Rising Water.

Approach: modified Dijkstra where the "cost" of a path is the maximum cell
elevation along it (the time you must wait before the whole path is
traversable), not the sum. Pop the cell with the smallest such max-elevation
from a min-heap; when we pop the bottom-right corner, that value is the
answer.

Invariant: when a cell is popped, its key is the minimum possible value of
max(elevation) over all paths from (0,0) to it. This holds because any other
path must leave the set of already-popped cells through some frontier edge,
whose max is at least the current heap-min (non-negative elevations only
raise a path's maximum, never lower it). Hence popping (n-1, n-1) yields the
earliest swim time.

Complexity: O(n^2 log n) time — n^2 cells, each pushed at most 4 times;
O(n^2) space for the heap and visited set.
"""
from __future__ import annotations

import heapq


class Solution:
    def swimInWater(self, grid: list[list[int]]) -> int:
        n = len(grid)
        # heap of (time_needed, row, col); time = max elevation on the path so far
        heap = [(grid[0][0], 0, 0)]
        seen = {(0, 0)}  # cells already reached with optimal time

        while heap:
            t, r, c = heapq.heappop(heap)
            if (r, c) == (n - 1, n - 1):
                return t  # first pop of the target is provably optimal
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < n and 0 <= nc < n and (nr, nc) not in seen:
                    seen.add((nr, nc))
                    # entering a new cell can only raise the path's max elevation
                    heapq.heappush(heap, (max(t, grid[nr][nc]), nr, nc))
        return -1  # unreachable for a well-formed grid; satisfies type checkers
