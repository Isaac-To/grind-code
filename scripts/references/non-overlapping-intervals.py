"""Reference solution — 435. Non-overlapping Intervals.

Approach: greedy "activity selection". To keep the maximum number of
non-overlapping intervals, sort by END time and repeatedly keep the
interval that finishes earliest; any interval starting before that end
overlaps it and must be removed. The answer is the count removed.

Why earliest-end is safe (invariant): after sorting by end, the first
kept interval leaves the most room for everything that comes after —
exchanging any optimal solution's first pick for the earliest-ending
interval never breaks feasibility, since that interval ends no later
and so conflicts with a subset of the same later intervals. Applying
the argument inductively makes the greedy choice optimal.

Note intervals that merely touch ([1,2] and [2,3]) do NOT overlap:
a later interval may start exactly at the last kept end.

Complexity: O(n log n) time for the sort; O(1) extra space (sorted()
uses O(n), an in-place alternative exists).
"""
from __future__ import annotations


class Solution:
    def eraseOverlapIntervals(self, intervals: list[list[int]]) -> int:
        # Sort by end time: the interval finishing earliest is always safe to keep.
        by_end = sorted(intervals, key=lambda iv: iv[1])

        removed = 0
        last_end = by_end[0][1]  # end of the most recently kept interval
        for start, end in by_end[1:]:
            if start < last_end:
                removed += 1      # overlaps a kept interval — must be discarded
            else:
                last_end = end     # disjoint (touching allowed) — keep it

        return removed
