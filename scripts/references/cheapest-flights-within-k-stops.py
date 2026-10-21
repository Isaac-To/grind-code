"""Reference solution — 787. Cheapest Flights Within K Stops.

Approach: Bellman-Ford limited to k+1 relaxation rounds. A route from src to
dst with at most k intermediate stops uses at most k+1 flights, so we relax
every edge exactly k+1 times, each round extending all cheapest paths by one
more flight. Crucially, each round must work from a *frozen snapshot* of the
distances — otherwise one round could chain several edges together and
secretly allow more stops than the budget permits.

Invariant: after round r, dist[v] is the cheapest fare to reach v using at
most r flights (i.e. r-1 stops). Copying dist before each round enforces this.
If dst is still "unreachable" (infinity) after k+1 rounds, no qualifying
route exists and we return -1.

Complexity: O(k * E) time — k+1 passes over all flights;
O(N) extra space per round for the snapshot.
"""
from __future__ import annotations


class Solution:
    def findCheapestPrice(self, n: int, flights: list[list[int]], src: int, dst: int, k: int) -> int:
        INF = float("inf")
        dist = [INF] * n  # cheapest fare found so far to each city
        dist[src] = 0

        # k stops  ->  at most k+1 flights  ->  k+1 relaxation rounds
        for _ in range(k + 1):
            snapshot = dist[:]  # freeze: each round extends paths by ONE flight
            updated = False
            for u, v, price in flights:
                if dist[u] != INF and dist[u] + price < snapshot[v]:
                    snapshot[v] = dist[u] + price  # reach v via u with one more flight
                    updated = True
            dist = snapshot
            if not updated:
                break  # no improvement this round: further rounds cannot help

        return dist[dst] if dist[dst] != INF else -1
