"""Reference solution — 5. Longest Palindromic Substring.

Approach: expand around every possible palindrome centre. A palindrome is
determined by its centre — either a single character (odd length) or the
gap between two characters (even length) — and its mirrors. There are
exactly 2n-1 centres in a string of length n; expanding each outward as far
as the characters match enumerates every palindromic substring.

Invariant: after all centres are tried, `best` holds a longest palindrome
found so far, and it is genuinely the maximum: any palindromic substring
has a unique centre, and full expansion from that centre must reach at
least its length.

Ties are broken by first occurrence (we only replace on strictly greater
length), which keeps the output deterministic — e.g. "babad" -> "bab".

Complexity: O(n^2) time (each of the 2n-1 centres may expand O(n) steps),
O(1) space besides the output slice.
"""
from __future__ import annotations


class Solution:
    def longestPalindrome(self, s: str) -> str:
        best = ""                      # longest palindrome found so far

        def expand(lo: int, hi: int) -> None:
            # grow the window [lo, hi] while it stays a palindrome
            while lo >= 0 and hi < len(s) and s[lo] == s[hi]:
                lo -= 1
                hi += 1
            # window overshot by one on each side; restore and maybe record
            nonlocal best
            if hi - lo - 1 > len(best):
                best = s[lo + 1:hi]

        for i in range(len(s)):
            expand(i, i)      # odd-length palindromes centred at i
            expand(i, i + 1)  # even-length palindromes centred between i, i+1
        return best
