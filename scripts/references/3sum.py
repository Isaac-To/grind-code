"""Reference solution — 15. 3Sum.

Approach: sort the array, then fix each first element `a` at index i
and run the classic two-pointer sweep for a pair summing to -a in
the remainder. Skip duplicate values both when choosing `a` and
inside the two-pointer sweep so each triplet appears exactly once.

Invariant: after sorting, all triplets (a, b, c) with a <= b <= c summing
to zero have a as their smallest element, so iterating i in ascending
order and searching the strictly-later suffix finds each *value
triplet* exactly once — duplicates are removed by never re-using a
value already fully processed at either level.

Why the two-pointer inner loop works: the suffix is sorted, so if
b + c is too small only a larger b can help (move lo up), and if too
large only a smaller c can help (move hi down) — the same shrinking
argument as Two Sum II, applied to a moving window.

Complexity: O(n^2) time — the outer loop runs n times and each inner
two-pointer sweep is linear; O(n) space for sorting's output (O(1) or
O(log n) auxiliary depending on the sort, plus the output itself).
"""
from __future__ import annotations


class Solution:
    def threeSum(self, nums: list[int]) -> list[list[int]]:
        nums = sorted(nums)          # enables the ordered two-pointer scan
        n = len(nums)
        triplets: list[list[int]] = []
        for i in range(n - 2):       # first (smallest) element of the triplet
            if nums[i] > 0:
                break                # smallest value positive -> sum cannot be 0
            if i > 0 and nums[i] == nums[i - 1]:
                continue             # same first value as last i: skip duplicates
            lo, hi = i + 1, n - 1    # search the strictly-later suffix
            target = -nums[i]        # need b + c == -a
            while lo < hi:
                pair = nums[lo] + nums[hi]
                if pair == target:
                    triplets.append([nums[i], nums[lo], nums[hi]])
                    lo += 1
                    hi -= 1
                    # Skip repeats of the just-used b and c values.
                    while lo < hi and nums[lo] == nums[lo - 1]:
                        lo += 1
                    while lo < hi and nums[hi] == nums[hi + 1]:
                        hi -= 1
                elif pair < target:
                    lo += 1          # need a bigger b
                else:
                    hi -= 1          # need a smaller c
        return triplets
