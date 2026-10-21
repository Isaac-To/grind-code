"""Reference solution — 1. Two Sum.

Approach: single pass with a hash map from value -> index of where we saw
it. For each element x, its needed partner target - x is looked up among
*previously seen* elements only, which guarantees the two indices differ.

Invariant: before processing nums[i], `seen` maps each value from
nums[0..i-1] to one of its indices. If (target - nums[i]) is in seen we
have a genuine pair (earlier index, i); otherwise nums[i] joins the map.
The problem guarantees exactly one answer, so first-found is the answer.

Complexity: O(n) time, O(n) space — beats the O(n^2) brute force.
"""
from __future__ import annotations


class Solution:
    def twoSum(self, nums: list[int], target: int) -> list[int]:
        seen: dict[int, int] = {}   # value -> index of an earlier occurrence
        for i, value in enumerate(nums):
            partner = target - value          # what we need to complete the pair
            if partner in seen:               # partner appeared before index i
                return [seen[partner], i]     # earlier index first
            seen[value] = i                   # record for future partners
        return []  # unreachable: exactly one answer is guaranteed
