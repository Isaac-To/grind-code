"""Reference solution — 743. Network Delay Time.

Approach: single-source shortest path with non-negative weights — Dijkstra's
algorithm with a min-heap keyed by arrival time. We settle nodes in increasing
order of their distance from `k`; the first time we pop a node we have found
its true earliest arrival, because any other route would pass through a node
already popped (with a smaller-or-equal distance) plus a non-negative edge.

Invariant: when a node is popped from the heap for the first time, its stored
distance is optimal. The answer is the largest of these optimal distances —
the moment the last node hears the signal. If some node is never popped,
the graph did not connect it to `k`, so we return -1.

Complexity: O(E log E) time — each edge can push one heap entry;
O(N + E) space for the adjacency list, heap and distance array.
"""
from __future__ import annotations

import heapq


class Solution:
    def networkDelayTime(self, times: list[list[int]], n: int, k: int) -> int:
        # adjacency list: u -> list of (travel_time, v)
        adj: list[list[tuple[int, int]]] = [[] for _ in range(n + 1)]  # 1-indexed nodes
        for u, v, w in times:
            adj[u].append((w, v))

        # dist[v] = best known arrival time at v; None means "not reached yet"
        dist: list[int | None] = [None] * (n + 1)
        dist[k] = 0
        heap = [(0, k)]  # (arrival_time, node), start node hears it at t=0

        while heap:
            t, u = heapq.heappop(heap)
            if dist[u] is not None and t > dist[u]:
                continue  # stale entry — a shorter route to u was found later
            for w, v in adj[u]:
                nt = t + w  # earliest arrival at v through u
                if dist[v] is None or nt < dist[v]:
                    dist[v] = nt
                    heapq.heappush(heap, (nt, v))

        # all n nodes 1..n must have been reached; answer is the slowest one
        reached = [dist[v] for v in range(1, n + 1) if dist[v] is not None]
        return max(reached) if len(reached) == n else -1
