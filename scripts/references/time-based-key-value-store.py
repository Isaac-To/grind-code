"""Reference solution — 981. Time Based Key-Value Store.

Approach: keep, per key, a list of (timestamp, value) pairs appended in set
order. The problem guarantees set timestamps are strictly increasing, so each
list is sorted by timestamp with no extra work. A get(key, t) then becomes
"rightmost pair with timestamp <= t", which is a classic binary search
(bisect_right gives the insertion point after all entries <= t; stepping one
left yields the newest qualifying pair).

Invariant: for a query t, all entries with timestamp <= t occupy list
prefix [0 : idx) and all larger ones [idx : end), where idx = bisect_right.
The answer is list[idx - 1] when idx > 0, else "" (nothing was set at or
before t).

Complexity: set O(1) amortized; get O(log k) for a key with k entries;
space O(total number of set calls).
"""
from __future__ import annotations

from bisect import bisect_right


class TimeMap:
    def __init__(self):
        # key -> parallel list of timestamps; values[i] was set at times[i]
        self.times: dict[str, list[int]] = {}
        self.values: dict[str, list[str]] = {}

    def set(self, key: str, value: str, timestamp: int) -> None:
        # timestamps are strictly increasing per key, so append keeps sorted order
        self.times.setdefault(key, []).append(timestamp)
        self.values.setdefault(key, []).append(value)

    def get(self, key: str, timestamp: int) -> str:
        entries = self.times.get(key)
        if not entries:
            return ""                 # key never set (or not set yet)
        # idx = count of entries with timestamp <= the query; bisect_right lands
        # after any run of equal timestamps, but set timestamps are unique anyway
        idx = bisect_right(entries, timestamp)
        if idx == 0:
            return ""                 # every entry is newer than the query
        return self.values[key][idx - 1]  # newest entry at or before the query
