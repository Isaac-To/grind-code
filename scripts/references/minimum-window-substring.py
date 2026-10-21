"""Reference solution — 76. Minimum Window Substring.

Approach: classic expand/shrink two-pointer window over s. `need` counts how
many of each char t demands (duplicates included); `missing` counts how many
*required* characters are still absent from the window. Expand `right` until
`missing` hits 0 (window covers t), then shrink from the left while the
window still covers t, recording the smallest covering window seen.

Invariants:
  - `missing == 0` iff the window contains every char of t with the required
    multiplicities: decrementing only crosses to -1 for the k-th required
    copy when all k copies are inside, and increments only restore demand
    when a genuinely required copy leaves.
  - `best_start/best_len` describe the shortest all-inclusive window found
    so far, because every covering window is eventually shrunk from the left
    exactly until dropping one more char would break coverage — so its
    minimal form is measured before the pointer moves on.

Note `missing` is checked *after* incrementing on shrink, i.e. we stop
shrinking once the window has just become invalid again — the last valid
position was already recorded.

Complexity: O(|s| + |t|) time — each character enters and leaves the window
at most once; O(charset) space.
"""
from __future__ import annotations


class Solution:
    def minWindow(self, s: str, t: str) -> str:
        if len(t) > len(s):
            return ""  # impossible: t has more characters than s

        need: dict[str, int] = {}
        for ch in t:
            need[ch] = need.get(ch, 0) + 1

        missing = len(t)      # total count of still-required characters
        best_start, best_len = 0, len(s) + 1  # best window found; len+1 = none yet
        start = 0

        for right, ch in enumerate(s):
            if need.get(ch, 0) > 0:
                missing -= 1        # this char is one t still wanted: cover it
            need[ch] = need.get(ch, 0) - 1  # surplus copies go negative

            while missing == 0:     # window covers t: try to shrink from left
                if right - start + 1 < best_len:
                    best_start, best_len = start, right - start + 1
                left = s[start]
                need[left] += 1
                if need[left] > 0:  # we just dropped a char t actually needed
                    missing += 1    # window no longer covers t
                start += 1

        return "" if best_len == len(s) + 1 else s[best_start:best_start + best_len]
