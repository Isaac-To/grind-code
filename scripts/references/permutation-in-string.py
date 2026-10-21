"""Reference solution — 567. Permutation in String.

Approach: fixed-size sliding window of length len(s1) over s2, comparing
letter-frequency counts. Two strings are permutations of each other iff
their 26-letter count vectors are equal, so s2 contains a permutation of
s1 iff some window of s2 has s1's count vector.

Invariant: `window_counts` always equals the frequency vector of the last
len(s1) characters of s2 processed. When we add s2[end] we drop s2[end - n]
in the same step, so the vector stays exactly the window's counts. Hence
`window_counts == need` fires exactly when the current window is a
permutation of s1 — no false positives or negatives.

Shortcut: if s2 is shorter than s1 no window fits, return False up front.

Complexity: O(len(s2)) time — each character enters and leaves the window
once, comparisons are O(26); O(1) space — two fixed 26-slot lists.
"""
from __future__ import annotations


class Solution:
    def checkInclusion(self, s1: str, s2: str) -> bool:
        n = len(s1)
        if n > len(s2):
            return False  # no window of length n fits in s2

        def counts(s: str) -> list[int]:
            vec = [0] * 26
            for ch in s:
                vec[ord(ch) - ord("a")] += 1
            return vec

        need = counts(s1)          # required frequency vector
        window = counts(s2[:n])    # frequency vector of the first window
        if window == need:
            return True
        for end in range(n, len(s2)):
            window[ord(s2[end]) - ord("a")] += 1        # char entering on the right
            window[ord(s2[end - n]) - ord("a")] -= 1    # char leaving on the left
            if window == need:
                return True
        return False
