"""Reference solution — 323. Number of Connected Components in an Undirected Graph.

Approach: union-find (disjoint set union) with path compression and union
by rank. Start with n singleton components; every edge that joins two
nodes with different roots merges two components into one, decreasing
the count. An edge whose endpoints already share a root changes nothing.

Invariant: `count` equals n minus the number of successful unions, i.e.
the exact number of distinct connected components at all times.

Complexity: O(E * α(n)) time — α is the inverse Ackermann, effectively
constant; O(n) space for parents and ranks.
"""
from __future__ import annotations


class Solution:
    def countComponents(self, n: int, edges: list[list[int]]) -> int:
        parent = list(range(n))            # each node starts as its own root
        rank = [0] * n                     # union by rank keeps trees shallow

        def find(x: int) -> int:
            while parent[x] != x:          # iterative find with path halving
                parent[x] = parent[parent[x]]  # point x at its grandparent
                x = parent[x]
            return x

        count = n                          # n singletons initially
        for u, v in edges:
            ru, rv = find(u), find(v)
            if ru == rv:                   # same component already: edge is redundant
                continue
            # attach the shallower tree under the deeper one
            if rank[ru] < rank[rv]:
                ru, rv = rv, ru
            parent[rv] = ru
            if rank[ru] == rank[rv]:       # equal depths: merged tree grew by one
                rank[ru] += 1
            count -= 1                     # two components became one
        return count
