"""Reference solution — 78. Subsets.

Approach: depth-first search over the *indices* of `nums`. At each step we
stand at index `start` and decide, for every index i >= start, whether the
next subset element is nums[i]. A shared `path` list grows as we descend and
shrinks as we return; a *copy* of it is recorded whenever we enter a new call,
so every prefix of every decision chain — including the empty prefix — is
emitted exactly once. Starting each loop at `start + 1` (never looking back)
guarantees each subset is generated in exactly one order, hence no
duplicates.

Invariant: on entry to dfs(start, path), `path` is a subset of nums[:start]
and every subset whose elements all lie at indices < start has already been
recorded. Recording path first and recursing right of the current index
covers every subset exactly once (there are 2^n of them).

Complexity: O(n * 2^n) time — 2^n subsets, each copied in O(n);
O(n) recursion depth (plus output).
"""
from __future__ import annotations


class Solution:
    def subsets(self, nums: list[int]) -> list[list[int]]:
        result: list[list[int]] = []

        def dfs(start: int, path: list[int]) -> None:
            result.append(path[:])  # record the current prefix — a full subset
            for i in range(start, len(nums)):
                path.append(nums[i])      # choose nums[i] as the next element
                dfs(i + 1, path)         # only consider indices right of i
                path.pop()              # undo the choice (backtrack)

        dfs(0, [])
        return result
