"""Reference solution — 252. Meeting Rooms.

Approach: a person can attend all meetings iff no two meetings overlap.
Sort the meetings by start time and check each adjacent pair: if a
meeting starts before the previous one ends, the two share time and
the answer is False.

Invariant: after sorting, any overlapping pair must be adjacent — if
meetings i < j overlap then meeting i+1 (which starts between their
starts) also overlaps meeting i or starts even later than j's start
while j had already begun, so checking neighbours is sufficient.

Edge cases: an empty list, or a single meeting, is trivially attendable
(the loop body never runs and we return True).

Complexity: O(n log n) time for the sort; O(n) space for the sorted copy.
"""
from __future__ import annotations

from typing import List


class Solution:
    def canAttendMeetings(self, intervals: List[List[int]]) -> bool:
        by_start = sorted(intervals)  # lexicographic sort = by start time

        for i in range(1, len(by_start)):
            # This meeting begins before the previous one finished -> conflict.
            if by_start[i][0] < by_start[i - 1][1]:
                return False
        return True
