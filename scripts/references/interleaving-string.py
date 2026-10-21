"""Reference solution — 97. Interleaving String.

Approach: dynamic programming over prefixes. Let dp[i][j] be True when
s3[:i+j] can be formed by interleaving s1[:i] and s2[:j].

Recurrence:
    dp[i][j] = (s1[i-1] == s3[i+j-1] and dp[i-1][j])
             or (s2[j-1] == s3[i+j-1] and dp[i][j-1])

The last character of s3's prefix must come from one of the two strings,
and whichever it came from, the rest of s3's prefix must interleave the
shortened pair — that is exactly the subproblem.

Invariant: dp[i][j] is correct for exactly the prefixes of length i and j;
cells reference only smaller indices, so a simple row-major fill works.

Pruning: lengths must satisfy len(s1) + len(s2) == len(s3), else False.

Space optimization: keep only one row of the table and roll it over i;
dp[j] before assignment is dp[i-1][j] ("row above"), after assignment it
becomes dp[i][j].

Base case: dp[0][0] = True; row 0 and column 0 are plain prefix checks.

Complexity: O(m*n) time, O(n) space.
"""
from __future__ import annotations


class Solution:
    def isInterleave(self, s1: str, s2: str, s3: str) -> bool:
        m, n = len(s1), len(s2)
        if m + n != len(s3):           # interleaving must use every character
            return False
        # dp[j] will mean: can s3[:i+j] interleave s1[:i] and s2[:j]?
        dp = [False] * (n + 1)
        dp[0] = True                  # two empty prefixes interleave to ""
        for j in range(1, n + 1):     # row 0: only s2 contributes
            dp[j] = dp[j - 1] and s2[j - 1] == s3[j - 1]
        for i in range(1, m + 1):
            dp[0] = dp[0] and s1[i - 1] == s3[i - 1]   # column 0: only s1
            for j in range(1, n + 1):
                taken_from_s1 = s1[i - 1] == s3[i + j - 1] and dp[j]      # dp[j] is row above
                taken_from_s2 = s2[j - 1] == s3[i + j - 1] and dp[j - 1]   # already this row
                dp[j] = taken_from_s1 or taken_from_s2
        return dp[n]
