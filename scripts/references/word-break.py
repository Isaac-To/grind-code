"""Reference solution — 139. Word Break.

Approach: dp[i] = True iff the prefix s[:i] can be segmented into
dictionary words. For each end position i, try every last word s[j:i]:
    dp[i] = OR over j < i of (dp[j] and s[j:i] in words)
because a valid segmentation of s[:i] ends with some final word, and
cutting it off must leave a valid segmentation of s[:j].

Invariant: after processing i, dp[i] is correct — every possible last word
length is tested, and dp[j] is already settled (j < i, induction on i).
dp[0] = True (the empty prefix needs no words).

Optimization: only test j >= i - max_word_len, since no dictionary word is
longer than that. Checking membership against a set is O(1) average.

Complexity: O(n^2 * L) time in the worst case (L = max word length, for
slicing/hashing), O(n + total dictionary size) space.
"""
from __future__ import annotations


class Solution:
    def wordBreak(self, s: str, wordDict: list[str]) -> bool:
        words = set(wordDict)                     # O(1) average lookups
        max_len = max(map(len, wordDict)) if wordDict else 0
        dp = [True] + [False] * len(s)            # dp[0]: empty prefix is free
        for i in range(1, len(s) + 1):            # i = end of prefix (exclusive)
            # last word starts at j; it cannot be longer than max_len
            for j in range(max(0, i - max_len), i):
                if dp[j] and s[j:i] in words:
                    dp[i] = True
                    break                         # one valid last word suffices
        return dp[len(s)]
