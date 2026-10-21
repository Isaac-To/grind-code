"""Reference solution — 973. K Closest Points to Origin.

Approach: keep a *max-heap* of size k holding the k closest points seen so
far, keyed by squared Euclidean distance (sqrt is monotonic, so skipping it
changes nothing and avoids float error). For each point:
  - if the heap has fewer than k points, push it;
  - otherwise, if the point is closer than the *farthest* kept point (the
    heap root), replace that root.

Invariant: after processing every point, the heap holds exactly the k
closest points — any evicted point is farther than all k survivors, so it
can never belong to the answer.

Complexity: O(n log k) time; O(k) space. (Output order is irrelevant: the
problem accepts any order.)
"""
import heapq


class Solution:
    def kClosest(self, points: list[list[int]], k: int) -> list[list[int]]:
        # entries: [-dist_sq, x, y] — negated distance makes the heap a
        # max-heap by distance, so the root is the farthest kept point
        heap = []
        for x, y in points:
            dist_sq = x * x + y * y        # squared distance: no sqrt, no floats
            if len(heap) < k:
                heapq.heappush(heap, [-dist_sq, x, y])
            elif -heap[0][0] > dist_sq:    # closer than the farthest kept point
                heapq.heapreplace(heap, [-dist_sq, x, y])
        return [[x, y] for _, x, y in heap]  # drop the distance keys
