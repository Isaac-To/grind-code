"""Reference solution — 115. Distinct Subsequences.

Approach: dynamic programming over prefixes. Let dp[i][j] be the number of
distinct subsequences of s[:i] that equal t[:j].

Recurrence:
  - Match case: if s[i-1] == t[j-1], we may spend s's last character to
    match t's last one, on top of any way of forming t[:j-1] from
    s[:i-1]:
        dp[i][j] += dp[i-1][j-1]
  - Skip case (always available): ignore s's last character entirely:
        dp[i][j] += dp[i-1][j]

Base cases: dp[i][0] = 1 (the empty subsequence — delete everything) and
dp[0][j>0] = 0 (nothing to build t from).

Invariant: dp[i][j] counts exactly the index-subsets of s[:i] spelling
t[:j]; characters keep their relative order, so extending prefixes is
sound — a way of matching t[:j-1] inside s[:i-1] plus the matched last
character yields a distinct way for (i, j), and every way arises so.

Space: roll over rows of s; iterate j downward so dp[j-1] is still the
previous row (01-knapsack reuse trick).

Complexity: O(len(s) * len(t)) time, O(len(t)) space.
"""
from __future__ import annotations


class Solution:
    def numDistinct(self, s: str, t: str) -> int:
        n = len(t)
        dp = [1] + [0] * n        # row i=0: only the empty t is formable
        for ch in s:              # extend s's prefix by one character
            # downward sweep keeps dp[j-1] = previous-row value
            for j in range(n, 0, -1):
                if ch == t[j - 1]:
                    dp[j] += dp[j - 1]   # spend ch matching t[j-1]
            # skipping ch needs no update: dp[j] already includes dp[i-1][j]
        return dp[n]
