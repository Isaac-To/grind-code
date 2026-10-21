"""Reference solution — 684. Redundant Connection.

Approach: incremental union-find. Add edges one at a time in input order;
the moment an edge connects two nodes that are *already* in the same
component, that edge closes a cycle and is the one to remove (processing
in order automatically yields the last such edge in the input).

Invariant: after processing k edges, the DSU partitions the nodes
exactly by the connected components of the first k edges. So the first
edge whose endpoints share a root is the first cycle-closing edge — and
because the graph has exactly one extra edge, it is the unique answer
that appears last.

Complexity: O(n * α(n)) time, effectively linear; O(n) space.
"""
from __future__ import annotations


class Solution:
    def findRedundantConnection(self, edges: list[list[int]]) -> list[int]:
        # node labels are 1..n, so index 0 is an unused dummy slot
        parent = list(range(len(edges) + 1))

        def find(x: int) -> int:
            while parent[x] != x:              # path halving keeps trees flat
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for u, v in edges:
            ru, rv = find(u), find(v)
            if ru == rv:                        # u and v already connected: cycle!
                return [u, v]                  # first such edge in order = answer
            parent[ru] = rv                    # merge the two components
        return []                              # unreachable: input guarantees a cycle
