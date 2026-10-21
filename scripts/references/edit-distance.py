"""Reference solution — 72. Edit Distance.

Approach: Levenshtein distance via 2-D dynamic programming. Let dp[i][j]
be the minimum number of insert/delete/replace operations turning
word1[:i] into word2[:j].

Recurrence:
  - If word1[i-1] == word2[j-1], the last characters align for free:
        dp[i][j] = dp[i-1][j-1]
  - Otherwise fix them with exactly one operation:
        replace: dp[i-1][j-1] + 1   (make the last chars equal, both consumed)
        delete : dp[i-1][j] + 1     (drop word1's last char, word2 unchanged)
        insert : dp[i][j-1] + 1     (append word2's last char to word1)
    take the minimum of the three.

Base cases: dp[i][0] = i (delete i chars), dp[0][j] = j (insert j chars).

Invariant: dp[i][j] is the exact edit distance of the two prefixes; every
cell only reads smaller indices, so row-major filling is safe.

Why it works: consider an optimal edit script for the prefixes. Look at
what it does with word1's last character: it either matches/replaces it
with word2's last character, deletes it, or inserts word2's last character
after it — the three cases above, each reducing to a strictly smaller
subproblem. The cases cover every script, so the min is optimal.

Space: two rolling rows, O(len(word2)).

Complexity: O(m*n) time, O(n) space.
"""
from __future__ import annotations


class Solution:
    def minDistance(self, word1: str, word2: str) -> int:
        m, n = len(word1), len(word2)
        prev = list(range(n + 1))          # row i=0: j inserts to build word2[:j]
        for i in range(1, m + 1):
            curr = [i] + [0] * n           # dp[i][0] = i deletes
            for j in range(1, n + 1):
                if word1[i - 1] == word2[j - 1]:
                    curr[j] = prev[j - 1]              # chars align, no cost
                else:
                    curr[j] = 1 + min(
                        prev[j - 1],   # replace word1[i-1] with word2[j-1]
                        prev[j],      # delete word1[i-1]
                        curr[j - 1],   # insert word2[j-1]
                    )
            prev = curr
        return prev[n]
