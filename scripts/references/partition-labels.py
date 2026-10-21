"""Reference solution — 763. Partition Labels.

Approach: greedy interval merging. First record `last[c]`, the last index of
each character — a part must extend at least to the last occurrence of every
character it contains.

Then scan once, maintaining `end`, the farthest last-occurrence among
characters seen so far in the current part. Invariant: the current part
cannot legally close before `end`, and at index i == end every character in
the part so far is exhausted — the earliest possible cut. Cutting as early as
possible maximizes the number of parts.

Complexity: O(n) time, O(1) space (at most 26 letters).
"""
from __future__ import annotations


class Solution:
    def partitionLabels(self, s: str) -> list[int]:
        last = {c: i for i, c in enumerate(s)}   # last occurrence of each char
        parts = []
        start = 0        # left edge of the current part
        end = 0           # required right edge so far (max of last occurrences)
        for i, c in enumerate(s):
            end = max(end, last[c])
            if i == end:              # no open character extends past here
                parts.append(i - start + 1)
                start = i + 1         # begin the next part
        return parts
