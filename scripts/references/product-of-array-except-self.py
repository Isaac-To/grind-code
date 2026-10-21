"""Reference solution — 238. Product of Array Except Self.

Approach: prefix/suffix products without division. answer[i] equals the
product of everything left of i times the product of everything right of
i. First sweep computes running prefix products into answer; the second
sweep multiplies in running suffix products from the right, using one
scalar — O(1) extra space beyond the output array.

Invariant: after the left sweep, answer[i] = product of nums[0..i-1]
(and answer[0] = 1, the empty product). During the right sweep, before
processing index i, `suffix` = product of nums[i+1..n-1]; so
answer[i] *= suffix leaves answer[i] = (product left of i) * (product
right of i) — exactly the required value. Zeros need no special casing:
a zero anywhere simply zeroes every answer except positions holding the
sole zero (which get the product of the rest).

Complexity: O(n) time, O(1) extra space (output excluded by convention).
"""
from __future__ import annotations


class Solution:
    def productExceptSelf(self, nums: list[int]) -> list[int]:
        n = len(nums)
        answer = [1] * n              # answer[i] starts as the empty product
        prefix = 1
        for i in range(n):            # left pass: product of nums[0..i-1]
            answer[i] = prefix        # everything strictly left of i
            prefix *= nums[i]         # extend prefix to include nums[i]
        suffix = 1
        for i in range(n - 1, -1, -1):  # right pass: fold in right side
            answer[i] *= suffix       # multiply by product of nums[i+1..end]
            suffix *= nums[i]         # extend suffix to include nums[i]
        return answer
