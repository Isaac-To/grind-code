"""Reference solution — 261. Graph Valid Tree.

Approach: a tree on n nodes is exactly a graph that is connected and
acyclic with n - 1 edges. Check the edge count first (cheap rejection:
too few edges can't connect, too many must contain a cycle), then verify
acyclicity-and-connectivity in one pass: run BFS from node 0 and reject
if we ever touch an already-visited node through a *non-parent* edge
(cycle) or if fewer than n nodes are reached (disconnected).

Invariant: the visited set grows only through tree edges; every node
reached was discovered exactly once. Reaching n visited nodes with n - 1
edges consumed and no repeats proves connected + acyclic = tree.

Complexity: O(V + E) time; O(V + E) space.
"""
from __future__ import annotations

from collections import deque


class Solution:
    def validTree(self, n: int, edges: list[list[int]]) -> bool:
        if len(edges) != n - 1:            # tree needs exactly n-1 edges
            return False

        adj: list[list[int]] = [[] for _ in range(n)]
        for u, v in edges:                # undirected: register both directions
            adj[u].append(v)
            adj[v].append(u)

        visited = {0}                      # start the BFS from node 0
        queue = deque([(0, -1)])           # (node, parent) to allow the edge back
        while queue:
            node, parent = queue.popleft()
            for nxt in adj[node]:
                if nxt == parent:          # the edge we arrived on — not a cycle
                    continue
                if nxt in visited:         # a second path to a node -> cycle
                    return False
                visited.add(nxt)
                queue.append((nxt, node))

        return len(visited) == n          # every node reached -> connected
