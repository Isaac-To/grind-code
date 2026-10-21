"""Reference solution — 46. Permutations.

Approach: classic backtracking with a "used" boolean mask. `path` holds the
partial permutation; for each position in the loop we try every element not
yet used, mark it, recurse, then unmark. Because the loop scans indices in
increasing order at every level, all n! orderings come out distinct.

Invariant: at any point, path holds k distinct elements of nums and used[i]
is True exactly when nums[i] is in path. When len(path) == n, path is a
complete permutation — record a copy.

Complexity: O(n * n!) time — n! leaves, each copied in O(n);
O(n) extra space (path + used), plus O(n) recursion depth.
"""
from __future__ import annotations


class Solution:
    def permute(self, nums: list[int]) -> list[list[int]]:
        result: list[list[int]] = []
        used = [False] * len(nums)  # used[i] <=> nums[i] is already in path
        path: list[int] = []

        def dfs() -> None:
            if len(path) == len(nums):
                result.append(path[:])  # every element placed — a permutation
                return
            for i in range(len(nums)):
                if used[i]:
                    continue  # nums[i] already placed earlier in the path
                used[i] = True
                path.append(nums[i])  # place nums[i] at the next open position
                dfs()
                path.pop()  # undo placement (backtrack)
                used[i] = False

        dfs()
        return result
