"""Reference solution — 33. Search in Rotated Sorted Array.

Approach: at any probe, the window [lo, hi] contains at most one rotation
"cliff", so at least one half of the window is perfectly sorted. Find that
sorted half (compare nums[lo] with nums[mid]); if the target lies within that
half's value range, search it — otherwise search the other half. A range test
on a sorted half is exact, so each probe discards half the window.

Invariant: the target's index, if it exists, always stays in [lo, hi].
  - If nums[lo] <= nums[mid] the left half [lo..mid] is sorted:
      target in [nums[lo], nums[mid]) -> hi = mid - 1, else lo = mid + 1.
  - Otherwise the right half [mid..hi] is sorted:
      target in (nums[mid], nums[hi]] -> lo = mid + 1, else hi = mid - 1.

The half-open comparisons (`<` / `>` on the far end) are safe because a hit
at mid itself is handled first — we never wrongly discard the target's own
index.

Complexity: O(log n) time; O(1) space.
"""
from __future__ import annotations


class Solution:
    def search(self, nums: list[int], target: int) -> int:
        lo, hi = 0, len(nums) - 1          # closed window containing the answer, if any
        while lo <= hi:                   # window still has candidates
            mid = (lo + hi) // 2
            if nums[mid] == target:
                return mid                # exact hit
            if nums[lo] <= nums[mid]:     # left half [lo..mid] is sorted (<=: mid can equal lo)
                if nums[lo] <= target < nums[mid]:
                    hi = mid - 1          # target's value fits inside the sorted left half
                else:
                    lo = mid + 1          # it must be in the rotated right half
            else:                         # right half [mid..hi] is sorted
                if nums[mid] < target <= nums[hi]:
                    lo = mid + 1          # target's value fits inside the sorted right half
                else:
                    hi = mid - 1          # it must be in the rotated left half
        return -1                         # window empty: target absent
