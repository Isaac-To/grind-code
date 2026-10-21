"""Reference solution — 153. Find Minimum in Rotated Sorted Array.

Approach: the array is a sorted array cut once and the two pieces swapped, so
exactly one "cliff" (the rotation point) exists, and the minimum sits right
after it. Comparing nums[mid] against nums[hi] tells us which side of the
cliff mid is on:
  - nums[mid] > nums[hi]: mid is in the left (higher) piece, so the minimum
    lies strictly right of mid -> lo = mid + 1.
  - nums[mid] < nums[hi]: mid is in the right (lower) piece; mid itself could
    BE the minimum, so shrink to [lo, mid] -> hi = mid.
  - equality can't happen (elements are unique; mid != hi while lo < hi).

Invariant: the minimum's index always stays inside the closed window [lo, hi].
The window strictly shrinks every iteration (lo = mid + 1 moves past mid;
hi = mid cuts at least the last element), so the loop terminates with
lo == hi pointing at the minimum.

Complexity: O(log n) time; O(1) space.
"""
from __future__ import annotations


class Solution:
    def findMin(self, nums: list[int]) -> int:
        lo, hi = 0, len(nums) - 1     # closed window; min's index is inside it
        while lo < hi:               # stop when one candidate remains
            mid = (lo + hi) // 2
            if nums[mid] > nums[hi]:
                lo = mid + 1         # mid is left of the cliff: min is right of it
            else:
                hi = mid             # mid is in the right piece: min is at mid or left
        return nums[lo]              # window collapsed to the minimum
