"""Reference solution — 128. Longest Consecutive Sequence.

Approach: dump all values into a hash set, then walk each *maximal* run
from its start. A value x starts a run iff x - 1 is not in the set —
otherwise the run through x was already reachable from a smaller start.
From each start, count upward while the next integer stays in the set.

Invariant: every consecutive run in the input has exactly one minimal
element, and the walk from that element visits the whole run. Since each
element is visited at most once across all walks (walks only begin at
run starts and never overlap), the total work is O(n).

Complexity: O(n) average time (hash set), O(n) space.
"""
from __future__ import annotations


class Solution:
    def longestConsecutive(self, nums: list[int]) -> int:
        values = set(nums)              # O(1) membership; also deduplicates
        best = 0
        for x in values:
            if x - 1 in values:         # not a run start — skip, avoid
                continue                # re-scanning runs repeatedly
            length = 1                  # x IS a minimal element of a run
            while x + length in values:  # extend the run upward
                length += 1
            best = max(best, length)    # keep the longest run found
        return best                     # 0 for an empty array
