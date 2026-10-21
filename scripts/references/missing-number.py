"""Reference solution — 268. Missing Number.

Approach: XOR the full expected range [0..n] against every element.
Each number that appears in `nums` appears once in the range too, so it
cancels (a ^ a = 0); the one range value with no partner — the missing
number — survives.

Invariant: `result` starts as 0 and folds in the expected value i and
the actual value nums[i] at each step, so every present value is
XOR-ed exactly twice and the missing value exactly once.

Complexity: O(n) time — single pass; O(1) extra space.
"""
from __future__ import annotations


class Solution:
    def missingNumber(self, nums: list[int]) -> int:
        n = len(nums)
        result = n                       # start with the range value n (no index for it)
        for i in range(n):
            result ^= i ^ nums[i]       # expected i pairs with actual nums[i]
        return result
