"""Reference solution — 332. Reconstruct Itinerary.

Approach: Hierholzer's algorithm for an Eulerian path, greedily biased toward
lexical order. Every ticket is a directed edge; a valid itinerary uses each
edge exactly once (an Eulerian path starting at "JFK"). Sort each airport's
outgoing destinations lexically and always fly to the smallest unused
destination; when stuck, backtrack, prepending airports to the route.

Invariant: greedily following the lexically smallest edge never breaks
Eulerian-path feasibility, and the postorder in which airports are appended
during the stuck/backtrack phase is exactly the itinerary reversed. Hence the
first complete route produced is the lexically smallest valid one. (Why
greedy is safe: if the smallest edge leads to a dead end that is not the final
airport, that dead-end component gets absorbed as a detour appended in the
middle — Hierholzer's classic argument — so no lexical choice is ever wasted.)

Complexity: O(E log E) time for sorting each destination list plus walking
every edge once; O(E) space for the graph, stacks and result.
"""
from __future__ import annotations

import heapq


class Solution:
    def findItinerary(self, tickets: list[list[str]]) -> list[str]:
        # adjacency as one lazy min-heap of destinations per airport:
        # popping yields destinations in lexical order without re-sorting
        graph: dict[str, heapq] = {}
        for src, dst in tickets:
            graph.setdefault(src, []).append(dst)
        for src in graph:
            heapq.heapify(graph[src])  # in-place, O(len)

        route: list[str] = []  # built backwards as airports dead-end
        stack = ["JFK"]  # current path from the start airport

        while stack:
            # while the current airport has an unused outgoing ticket,
            # keep flying (greedily to the lexically smallest destination)
            while graph.get(stack[-1]):
                stack.append(heapq.heappop(graph[stack[-1]]))
            # stuck: no unused tickets leave here — this airport is finalized,
            # so it belongs at the front of the remaining suffix
            route.append(stack.pop())

        route.reverse()  # we appended right-to-left; reverse to travel order
        return route
