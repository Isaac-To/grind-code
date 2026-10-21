"""Reference solution — 152. Maximum Product Subarray.

Approach: products behave differently from sums — a negative number flips
the sign, so a very negative running product can become the maximum when
multiplied by another negative. Therefore track BOTH the largest and the
smallest product of a subarray ending at the current index:
    cand_hi = max(x, hi * x, lo * x)
    cand_lo = min(x, lo * x, hi * x)
where x = nums[i]. Starting fresh at x covers the subarray beginning here.

Invariant: after step i, `hi`/`lo` are the max/min product over ALL subarrays
ending exactly at i. Any such subarray is x alone, or (a subarray ending at
i-1) * x — and extending the previous extreme products plus starting fresh
enumerates all three cases. The global answer is the max of the per-index
`hi` values.

A zero resets both extremes harmlessly: extending through 0 gives 0, and
starting fresh at the next element is covered by the `x` candidate.

Complexity: O(n) time, O(1) space.
"""
from __future__ import annotations


class Solution:
    def maxProduct(self, nums: list[int]) -> int:
        best = hi = lo = nums[0]      # best = answer so far; hi/lo end at i
        for x in nums[1:]:
            candidates = (x, hi * x, lo * x)   # start fresh, or extend either extreme
            hi, lo = max(candidates), min(candidates)
            best = max(best, hi)
        return best
