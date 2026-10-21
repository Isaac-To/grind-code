"""Reference solution — 253. Meeting Rooms II.

Approach: sweep-line over "events". Turn each meeting [s, e) into two
events: +1 room at time s, -1 room at time e. Sort the events by time
(ties: releases before acquisitions — a meeting ending exactly when
another starts frees the room for it) and track how many rooms are in
use; the answer is the peak concurrency.

Invariant: after processing all events with time <= t, the running
counter equals the number of meetings whose start <= t and end > t
that we have opened minus the ones already released — i.e. exactly the
concurrency at time t. The answer is the maximum this counter reaches.

Alternative (equally classic): sort starts and ends separately into
two pointers and count how many meetings are "open" — this is the
same sweep written with two arrays.

Complexity: O(n log n) time for sorting the events; O(n) space.
"""
from __future__ import annotations

from typing import List


class Solution:
    def minMeetingRooms(self, intervals: List[List[int]]) -> int:
        events: list[tuple[int, int]] = []
        for start, end in intervals:
            events.append((start, 1))   # a meeting opens -> need one more room
            events.append((end, -1))    # a meeting closes -> free one room

        # Ties on time: -1 before +1 so back-to-back meetings share a room.
        events.sort(key=lambda ev: (ev[0], ev[1]))

        rooms = 0   # rooms in use right now
        peak = 0    # maximum rooms ever in use
        for _, delta in events:
            rooms += delta
            peak = max(peak, rooms)

        return peak
