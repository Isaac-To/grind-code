"""Reference solution — 57. Insert Interval.

Approach: single left-to-right sweep over the already-sorted intervals,
split into three phases. (1) Every interval that ends strictly before
newInterval starts cannot overlap it — copy it across untouched.
(2) Every interval that starts at or before newInterval's end overlaps
it (the list is sorted, so once an interval starts past the end no
later one can overlap either) — absorb it by widening newInterval to
the union's min start / max end. (3) Append the merged interval, then
copy the remaining untouched tail.

Invariant: `new` (a working copy of newInterval) always covers exactly
the union of every interval absorbed so far plus the original
newInterval, so after phase (2) it is the single merged interval the
problem asks for. Sorting order is preserved because we emit intervals
in the order we meet them, and `new` starts no later than any absorbed
interval (the input prefix ended before it) and ends before the tail.

Complexity: O(n) time — each interval is visited once; O(1) extra
space beyond the output list.
"""
from __future__ import annotations


class Solution:
    def insert(self, intervals: list[list[int]], newInterval: list[int]) -> list[list[int]]:
        result: list[list[int]] = []
        new_start, new_end = newInterval
        i, n = 0, len(intervals)

        # Phase 1: intervals entirely to the left — no contact with the new one.
        while i < n and intervals[i][1] < new_start:
            result.append(intervals[i])
            i += 1

        # Phase 2: intervals overlapping `new` — absorb each into it.
        while i < n and intervals[i][0] <= new_end:
            new_start = min(new_start, intervals[i][0])  # union's left edge
            new_end = max(new_end, intervals[i][1])      # union's right edge
            i += 1
        result.append([new_start, new_end])               # the merged interval

        # Phase 3: everything left over is already strictly to the right.
        while i < n:
            result.append(intervals[i])
            i += 1

        return result
