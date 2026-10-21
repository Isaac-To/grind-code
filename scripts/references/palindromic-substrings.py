"""Reference solution — 647. Palindromic Substrings.

Approach: every palindromic substring is determined by its centre — a single
character (odd length) or the gap between two adjacent characters (even
length). There are exactly 2n-1 centres; expanding each outward while the
mirror characters match counts every palindromic substring exactly once,
because a palindrome has a unique centre.

Invariant: `total` increases by exactly the number of palindromic substrings
whose centre is the one currently being expanded (each successful expansion
step is one more nested palindrome sharing that centre).

Complexity: O(n^2) time, O(1) space.
"""
from __future__ import annotations


class Solution:
    def countSubstrings(self, s: str) -> int:
        total = 0

        def expand(lo: int, hi: int) -> int:
            found = 0
            # each successful step = one more palindrome with this centre
            while lo >= 0 and hi < len(s) and s[lo] == s[hi]:
                found += 1
                lo -= 1
                hi += 1
            return found

        for i in range(len(s)):
            total += expand(i, i)      # odd-length palindromes
            total += expand(i, i + 1)  # even-length palindromes
        return total
