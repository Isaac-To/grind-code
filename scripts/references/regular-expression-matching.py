"""Reference solution — 10. Regular Expression Matching.

Approach: 2-D dynamic programming over prefixes. dp[i][j] = True when
s[:i] matches the pattern p[:j] fully.

Rules handled: '.' matches any single char; 'x*' matches zero or more x
(and '.*' zero or more of anything). The pattern is consumed in chunks:
either a single literal/dot, or a letter+'*' pair.

Recurrence for dp[i][j] with p[j-1] in mind:
  - p[j-1] == '*': the pair p[j-2]p[j-1] may match ZERO characters of s
        dp[i][j] = dp[i][j-2]
    or one more character, allowed only if p[j-2] is '.' or equals s[i-1]:
        dp[i][j] |= dp[i-1][j]   (star keeps absorbing s's characters)
  - otherwise a plain symbol must match s[i-1] (equal or '.'):
        dp[i][j] = dp[i-1][j-1]

Base cases: dp[0][0] = True; dp[i>0][0] = False (empty pattern matches only
empty s); dp[0][j] is True only when p[:j] is a chain of 'x*' pairs that
can all match zero characters.

Invariant: each cell's truth depends only on cells with a smaller i+j, so
row-major filling computes every subproblem before it is needed.

Complexity: O(len(s) * len(p)) time, O(len(p)) space with a rolling row.
"""
from __future__ import annotations


class Solution:
    def isMatch(self, s: str, p: str) -> bool:
        m, n = len(s), len(p)
        # dp[j] represents dp[i][j] for the current i; row 0 first:
        dp = [False] * (n + 1)
        dp[0] = True
        for j in range(2, n + 1):        # empty s vs pattern of 'x*' pairs
            dp[j] = p[j - 1] == '*' and dp[j - 2]
        for i in range(1, m + 1):
            prev = dp[:]                 # snapshot: dp[i-1][j] values
            dp[0] = False               # non-empty s never matches empty pattern
            for j in range(1, n + 1):
                pc = p[j - 1]
                if pc == '*':
                    zero = dp[j - 2]                      # star matches nothing
                    one = prev[j] and (p[j - 2] == '.' or p[j - 2] == s[i - 1])
                    dp[j] = zero or one                   # zero or one-more
                else:
                    dp[j] = prev[j - 1] and (pc == '.' or pc == s[i - 1])
        return dp[n]
