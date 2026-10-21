"""Reference solution — 1143. Longest Common Subsequence.

Approach: classic 2-D dynamic programming. Let dp[i][j] be the length of
the longest common subsequence of text1[:i] and text2[:j].

Recurrence:
  - If text1[i-1] == text2[j-1], that character can always end an optimal
    common subsequence of the two prefixes, so
        dp[i][j] = dp[i-1][j-1] + 1
  - Otherwise the two last characters cannot both be used, so at least one
    is irrelevant:
        dp[i][j] = max(dp[i-1][j], dp[i][j-1])

Base case: dp[0][*] = dp[*][0] = 0 — an empty string shares nothing.

Invariant: dp[i][j] is the LCS length of exactly the prefixes of length i
and j; each cell only ever looks at cells with strictly smaller indices,
so the table fills in increasing i, j order without cycles.

Why it works: the equal-character case is safe because any common
subsequence can be rearranged so that matching characters pair up in order;
if the optimal answers for the shorter prefixes matched different letters,
extending both by the same letter never hurts. The max case exhaustively
covers "drop the last character of one string or the other".

Space: keep only two rows (previous and current), O(min(len)) columns.

Complexity: O(len1 * len2) time, O(min(len1, len2)) space.
"""
from __future__ import annotations


class Solution:
    def longestCommonSubsequence(self, text1: str, text2: str) -> int:
        # Make text2 the shorter string so the rolling rows are small.
        if len(text2) > len(text1):
            text1, text2 = text2, text1
        prev = [0] * (len(text2) + 1)   # dp row for text1[:0] — all zeros
        for ch1 in text1:               # extend the text1 prefix by ch1
            curr = [0] * (len(text2) + 1)
            for j, ch2 in enumerate(text2, start=1):
                if ch1 == ch2:
                    curr[j] = prev[j - 1] + 1   # match: extend diagonal LCS
                else:
                    # drop ch1 (prev[j]) or drop ch2 (curr[j-1]) — take best
                    curr[j] = max(prev[j], curr[j - 1])
            prev = curr                 # current row becomes "previous"
        return prev[-1]                 # LCS of the full strings
