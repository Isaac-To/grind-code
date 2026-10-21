"""Reference solution — 242. Valid Anagram.

Approach: two strings are anagrams iff they use every character the same
number of times. Count characters with a hash map and compare the counts.

Invariant: after processing, `counts[c]` = (#occurrences of c in s) −
(#occurrences of c in t). The strings are anagrams iff every count is 0.
A cheap early exit: different lengths can never match.

For lowercase-only input a fixed 26-slot array works; collections.Counter
generalizes to any alphabet (Unicode included — the follow-up answer is
simply "use the same hash-map counting").

Complexity: O(n) time, O(1) space (at most 26 / alphabet-size buckets).
"""
from __future__ import annotations


class Solution:
    def isAnagram(self, s: str, t: str) -> bool:
        if len(s) != len(t):        # different sizes -> cannot be anagrams
            return False
        counts: dict[str, int] = {}
        for ch in s:                # add +1 for every char of s
            counts[ch] = counts.get(ch, 0) + 1
        for ch in t:                # subtract 1 for every char of t
            counts[ch] = counts.get(ch, 0) - 1
            if counts[ch] < 0:      # t used ch more often than s did
                return False
        # lengths are equal, so no count can be positive without some
        # count being negative first — hence all counts are exactly 0.
        return True
