"""Reference solution — 22. Generate Parentheses.

Approach: build the string one character at a time, tracking how many
`open` and `close` parentheses remain. At each step we may append '(' if
open > 0, and ')' only if close > open (closing before matching would make
the prefix invalid). A complete string has length 2n.

Invariant: every prefix of any generated string never closes more than it
opens (close > open check) and never exceeds n opens — these two conditions
are exactly the definition of a well-formed string, so every leaf is valid
and every valid string is reachable (the two greedy choices cover both).

Complexity: the number of strings is the n-th Catalan number, each built in
O(n) — O(4^n / sqrt(n)) total time; O(n) recursion depth.
"""
from __future__ import annotations


class Solution:
    def generateParenthesis(self, n: int) -> list[str]:
        result: list[str] = []

        def dfs(open: int, close: int, s: list[str]) -> None:
            if len(s) == 2 * n:
                result.append("".join(s))  # all n pairs placed — a valid string
                return
            if open < n:            # we can still afford another '('
                s.append("(")
                dfs(open + 1, close, s)
                s.pop()             # backtrack
            if close < open:        # a ')' must match an unmatched '('
                s.append(")")
                dfs(open, close + 1, s)
                s.pop()

        dfs(0, 0, [])
        return result
