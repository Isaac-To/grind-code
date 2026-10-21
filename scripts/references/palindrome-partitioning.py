"""Reference solution — 131. Palindrome Partitioning.

Approach: DFS over cut positions. `start` is the index where the next
partition piece begins; we try every end e such that s[start:e] is a
palindrome, append that piece, and recurse from e. When start reaches
len(s), every character is covered and `path` is a full partition — all of
whose pieces were checked to be palindromes on the way down.

Invariant: path is always a list of palindromic pieces covering exactly
s[:start]. Each partition is generated once because pieces are tried in
increasing order of cut position (no reordering possible).

Complexity: O(n * 2^n) worst case (all-equal string: every cut pattern is
palindromic); each palindrome check costs O(n) without memo, giving
O(n^2 * 2^n) here — fine for n <= 16. O(n) recursion depth.
"""
from __future__ import annotations


class Solution:
    def partition(self, s: str) -> list[list[str]]:
        result: list[list[str]] = []

        def is_palindrome(sub: str) -> bool:
            return sub == sub[::-1]  # a string equals its reverse

        def dfs(start: int, path: list[str]) -> None:
            if start == len(s):
                result.append(path[:])  # whole string covered by palindrome pieces
                return
            for end in range(start + 1, len(s) + 1):
                piece = s[start:end]
                if not is_palindrome(piece):
                    continue  # only palindrome pieces may enter the partition
                path.append(piece)
                dfs(end, path)  # next piece starts where this one ended
                path.pop()  # backtrack

        dfs(0, [])
        return result
