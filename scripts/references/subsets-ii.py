"""Reference solution — 90. Subsets II.

Approach: sort nums, then DFS over indices with the "skip duplicates at the
same tree level" rule. Inside one loop iteration, if nums[i] == nums[i-1]
and i > start, we skip: an equal value already started a branch at this
level, so starting another would duplicate the subsets it generates. Taking
the same value deeper in the path (i == start) remains allowed — that is how
[1, 2, 2] is produced from [1, 2, 2].

Invariant: each subset is emitted exactly once, in nondecreasing order.
Counting subsets of a run of k equal values: at each tree level we either
start with the value (once) or skip it entirely, giving k + 1 choices of
multiplicity — no combination of multiplicities is repeated.

Complexity: O(n * 2^n) time in the worst case (all distinct); O(n) depth.
"""
from __future__ import annotations


class Solution:
    def subsetsWithDup(self, nums: list[int]) -> list[list[int]]:
        nums = sorted(nums)  # equal values become adjacent — needed by the rule
        result: list[list[int]] = []

        def dfs(start: int, path: list[int]) -> None:
            result.append(path[:])  # the current prefix is itself a subset
            for i in range(start, len(nums)):
                if i > start and nums[i] == nums[i - 1]:
                    continue  # same value already used at this level — skip
                path.append(nums[i])   # extend the subset with nums[i]
                dfs(i + 1, path)      # only indices right of i
                path.pop()            # backtrack

        dfs(0, [])
        return result
