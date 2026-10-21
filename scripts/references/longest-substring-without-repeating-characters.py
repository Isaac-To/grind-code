"""Reference solution — 3. Longest Substring Without Repeating Characters.

Approach: sliding window with a hash map from character to its most recent
index. The window `s[start..right]` is always duplicate-free. When the new
character at `right` was already seen *inside* the window, jump `start` to
just past that previous occurrence; otherwise the window simply grows.

Invariant: after processing index `right`, `start` is the smallest index such
that s[start..right] has no duplicates. Why: we only move start forward to
`seen[char] + 1` when the old occurrence lies at or after start (an occurrence
before start is irrelevant — it's already outside the window and must not
drag start backwards, hence the `max`). Taking the running max of
`right - start + 1` therefore measures every maximal duplicate-free window.

Complexity: O(n) time — each index is visited once by `right` and `start`
only advances; O(min(n, alphabet)) space for the map.
"""
from __future__ import annotations


class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        seen: dict[str, int] = {}  # char -> index of its latest occurrence
        start = 0                  # left edge of the current duplicate-free window
        best = 0
        for right, char in enumerate(s):
            if char in seen and seen[char] >= start:
                # Previous occurrence is inside the window: shrink past it.
                start = seen[char] + 1
            seen[char] = right     # record/refresh the latest position
            best = max(best, right - start + 1)
        return best
