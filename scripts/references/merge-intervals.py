"""Reference solution — 56. Merge Intervals.

Approach: sort by start, then sweep once keeping a single "open"
interval. For each interval, either it starts after the open interval
ends (disjoint — commit the open one and open a new one) or it
overlaps/touches it (extend the open interval's right edge to the max
of the two ends; sorting guarantees its start is already the smaller).

Invariant: the open interval always equals the exact union of every
interval seen so far that overlaps the current group — because the
input is sorted by start, any interval that could overlap the group
must start no later than the group's current right edge, so the
max-end update never misses a merge.

Complexity: O(n log n) time dominated by the sort; O(n) space for the
output (O(log n)–O(n) for the sort itself, implementation-dependent).
"""
from __future__ import annotations


class Solution:
    def merge(self, intervals: list[list[int]]) -> list[list[int]]:
        # Sort by start so any overlapping interval of the current group
        # is adjacent in this order.
        intervals_sorted = sorted(intervals, key=lambda iv: iv[0])

        merged: list[list[int]] = []
        for start, end in intervals_sorted:
            if not merged or merged[-1][1] < start:
                # Disjoint from the last committed interval: start a new group.
                merged.append([start, end])
            else:
                # Overlaps (or touches) the open group: extend its right edge.
                # Touching ([1,4] + [4,5]) counts as overlapping per the problem.
                merged[-1][1] = max(merged[-1][1], end)

        return merged
