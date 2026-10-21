"""Reference solution — 53. Maximum Subarray.

Approach: Kadane's algorithm, a greedy/DP hybrid. Scan left to right while
tracking `cur` — the best sum of a subarray that *ends exactly here* — and
`best`, the best sum seen anywhere.

Invariant: after visiting index i, `cur` equals the maximum sum of any
subarray ending at i. Either the previous run is worth extending
(cur > 0 means nums[i] + cur > nums[i]) or it is dead weight and we restart
the subarray at nums[i]. `best` only ever updates from `cur`, so by the end
it holds the maximum over all end positions, i.e. over all subarrays.

Why it works: every subarray ends somewhere, so scanning all end positions
with the optimal ending-here value covers every candidate.

Complexity: O(n) time, O(1) space.
"""
from __future__ import annotations


class Solution:
    def maxSubArray(self, nums: list[int]) -> int:
        best = cur = nums[0]          # subarray ending at index 0 is just nums[0]
        for x in nums[1:]:
            # Extend the running subarray only if it adds value; else restart at x.
            cur = max(cur + x, x)
            best = max(best, cur)     # best over all end positions so far
        return best
