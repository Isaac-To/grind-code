"""Reference solution — 1584. Min Cost to Connect All Points.

Approach: Prim's minimum spanning tree with a min-heap of candidate edges.
Grow one connected component starting from point 0: repeatedly take the
cheapest edge from the component to an outside point, absorb that point, and
push its distances to all still-outside points. This is a dense complete
graph, so Prim with a heap (O(E log V), E = V^2) beats Kruskal's sort.

Invariant (cut property): at every step the cheapest edge crossing the cut
between the component and its complement belongs to *some* MST; adding it
keeps the partial tree a subtree of an MST. The sum of these V-1 choices is
therefore the minimum possible total cost.

Complexity: O(V^2 log V) time — up to V^2 heap pushes; O(V^2) space for the
heap in the worst case.
"""
from __future__ import annotations

import heapq


class Solution:
    def minCostConnectPoints(self, points: list[list[int]]) -> int:
        n = len(points)
        if n <= 1:
            return 0  # a single point (or none) needs no connections

        in_tree = [False] * n  # has this point joined the component yet?
        # heap of (cost, point_index): cheapest edge from the component outward
        heap = [(0, 0)]  # start from point 0; joining it costs nothing
        total = 0
        joined = 0  # how many points are in the component so far

        while joined < n:
            cost, i = heapq.heappop(heap)
            if in_tree[i]:
                continue  # stale entry — point already absorbed via cheaper edge
            in_tree[i] = True
            joined += 1
            total += cost  # pay for the cheapest edge that reached point i
            xi, yi = points[i]
            for j in range(n):
                if not in_tree[j]:
                    # Manhattan distance to the new frontier member
                    d = abs(xi - points[j][0]) + abs(yi - points[j][1])
                    heapq.heappush(heap, (d, j))

        return total
