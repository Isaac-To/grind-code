"""Reference solution — 424. Longest Repeating Character Replacement.

Approach: non-shrinking sliding window. For each window, the key quantity is
`window_len - count_of_most_frequent_char` = number of replacements needed to
make the whole window one uniform letter. The window is valid while that
quantity is <= k.

Invariant: the answer is the largest window length that ever satisfied the
validity condition, and `best` never decreases. We grow the window on every
step; when it becomes invalid we slide it forward *without shrinking* (start
and end both advance by one). This works because:
  - a window of length L was valid at some point iff `best` reached L,
  - and if length L is achievable, every smaller length is too (any valid
    window contains a valid sub-window), so never revisiting smaller lengths
    can't hide the answer.
We may keep a *stale* max-frequency (not recounting on shrink) because
`window_len - max_freq` only ever *underestimates* validity for lengths
already beaten by `best`; the true maximum window still gets measured
correctly when its frequencies are current.

Complexity: O(n) time — both pointers advance monotonically, counting is
O(26) per step; O(1) space — fixed 26-slot counter.
"""
from __future__ import annotations


class Solution:
    def characterReplacement(self, s: str, k: int) -> int:
        counts: dict[str, int] = {}  # char -> occurrences inside the window
        max_freq = 0                  # highest single-char count seen (may lag)
        start = 0
        best = 0
        for end, char in enumerate(s):
            counts[char] = counts.get(char, 0) + 1
            max_freq = max(max_freq, counts[char])  # candidate for the dominant letter
            window_len = end - start + 1
            if window_len - max_freq > k:
                # Window needs more than k replacements: slide, don't shrink.
                counts[s[start]] -= 1
                start += 1
            # Whether or not we slid, the window length is `end - start + 1`
            # (unchanged by a one-step slide of both edges).
            best = end - start + 1
        return best
