"""Reference solution — 1046. Last Stone Weight.

Approach: simulate the game with a *max-heap* of negated weights, so the two
largest stones are always available in O(log n). Pop the two heaviest stones
y (heavier) and x (lighter). If they differ, push y - x back; if equal, both
vanish. Repeat until at most one stone remains.

Invariant: heapq implements a min-heap, so we store negatives — popping the
root yields the *heaviest* stone. Each smash removes two stones and adds at
most one, so the loop terminates; the final stone's weight (0 if none) is
the answer.

Complexity: O(n log n) time — n-1 smashes, each O(log n); O(n) space.
"""
import heapq


class Solution:
    def lastStoneWeight(self, stones: list[int]) -> int:
        # negate so the min-heap's root is the heaviest stone
        heap = [-w for w in stones]
        heapq.heapify(heap)
        while len(heap) > 1:
            y = -heapq.heappop(heap)   # heaviest stone
            x = -heapq.heappop(heap)   # second heaviest, x <= y
            if x != y:                # equal stones annihilate; unequal leave y - x
                heapq.heappush(heap, -(y - x))
        return -heap[0] if heap else 0  # last stone's weight, or 0 if none remain
