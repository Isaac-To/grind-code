"""Reference solution — 1851. Minimum Interval to Include Each Query.

Approach: offline processing with a min-heap. Sort the intervals by
start and sort the queries (keeping each query's original index). Sweep
the queries in increasing order: before answering query q, push every
interval with start <= q onto a min-heap keyed by SIZE
(right - left + 1); those are the candidates that contain q. Then pop
every heap-top interval whose right edge < q — a popped interval ends
before q, and since queries only grow, it can never contain any later
query either, so discarding it is permanent. The new heap top is the
smallest containing interval.

Invariant: at the moment query q is answered, the heap holds exactly
the intervals with left <= q and right >= q, ordered by size; hence its
top is the minimum-size interval containing q, and -1 if the heap is
empty.

Complexity: each interval is pushed and popped at most once, so
O(n log n + m log m) time for the two sorts plus O((n + m) log n) heap
work; O(n + m) space.
"""
from __future__ import annotations

import heapq


class Solution:
    def minInterval(self, intervals: list[list[int]], queries: list[int]) -> list[int]:
        intervals_by_start = sorted(intervals)  # feed candidates in start order
        indexed_queries = sorted(enumerate(queries), key=lambda p: p[1])

        answer = [0] * len(queries)
        heap: list[tuple[int, int]] = []  # (size, right_end)
        i = 0  # next interval not yet offered to the heap

        for original_index, q in indexed_queries:
            # Offer every interval that has started by time q.
            while i < len(intervals_by_start) and intervals_by_start[i][0] <= q:
                left, right = intervals_by_start[i]
                heapq.heappush(heap, (right - left + 1, right))
                i += 1
            # Retire intervals that already ended strictly before q.
            while heap and heap[0][1] < q:
                heapq.heappop(heap)
            # Heap top is now the smallest interval containing q, if any.
            answer[original_index] = heap[0][0] if heap else -1

        return answer
