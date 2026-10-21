"""Reference solution — 17. Letter Combinations of a Phone Number.

Approach: plain cartesian-product DFS. Walk the digits left to right; at
each level append one of the letters mapped to the current digit, recurse on
the rest, then pop (backtrack). Every combination of choices — one letter per
digit — is generated exactly once, in digit order.

Invariant: `path` holds one chosen letter for each of the first k digits.
When k == len(digits), path is a complete combination; recording a copy
freezes it before further backtracking mutates the list.

Complexity: O(4^d * d) time for d digits (digits 7 and 9 map to 4 letters,
so 4^d leaves, each of length d); O(d) recursion depth.
"""
from __future__ import annotations


class Solution:
    # Digit-to-letters mapping as on a telephone keypad (1 and 0 map to none).
    LETTERS = {
        "2": "abc", "3": "def", "4": "ghi", "5": "jkl",
        "6": "mno", "7": "pqrs", "8": "tuv", "9": "wxyz",
    }

    def letterCombinations(self, digits: str) -> list[str]:
        if not digits:
            return []  # no digits: LeetCode expects [], not [""]
        result: list[str] = []
        path: list[str] = []

        def dfs(i: int) -> None:
            if i == len(digits):
                result.append("".join(path))  # one letter chosen per digit
                return
            for ch in self.LETTERS[digits[i]]:  # choices for digit i
                path.append(ch)
                dfs(i + 1)  # move on to the next digit
                path.pop()  # backtrack

        dfs(0)
        return result
