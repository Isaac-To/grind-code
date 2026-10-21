"""Reference solution — 213. House Robber II (circular street).

Approach: the houses form a circle, so robbing the first house forbids the
last (they are neighbours) and vice versa. Every optimal plan therefore
falls into exactly one of two linear subproblems:
  * houses 0 .. n-2  (first may be robbed, last excluded), or
  * houses 1 .. n-1  (first excluded, last may be robbed).
Running the linear House Robber DP on each slice and taking the max covers
all plans; a plan robbing neither end is contained in both slices.

Edge case n == 1: both slices would be empty, so return nums[0] directly.

Invariant: the two-open-ended DP (helper below) is correct for a linear
street; slicing the circle at the first/last house turns the circular
constraint into two linear instances whose union contains every valid plan.

Complexity: O(n) time (two linear passes), O(1) extra space.
"""
from __future__ import annotations


class Solution:
    def rob(self, nums: list[int]) -> int:
        if len(nums) == 1:          # both slices would be empty
            return nums[0]

        def rob_linear(houses: list[int]) -> int:
            skip, robbed = 0, 0     # best loot ending without / with previous
            for money in houses:
                skip, robbed = robbed, max(robbed, skip + money)
            return robbed

        # compare plans that exclude the last house vs. exclude the first
        return max(rob_linear(nums[:-1]), rob_linear(nums[1:]))
