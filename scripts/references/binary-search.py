"""Reference solution — 704. Binary Search.

Approach: classic binary search over an ascending, strictly distinct array.
Maintain a *closed* window [lo, hi] that always contains the target's index
if the target exists at all.

Invariant: every index < lo has been proven too small, every index > hi
too large. Each probe at the midpoint `mid` discards half the window:
  - nums[mid] < target  -> the answer, if any, is right of mid, so lo = mid + 1
  - nums[mid] > target  -> the answer, if any, is left of mid, so hi = mid - 1
  - nums[mid] == target -> found, return mid

The loop ends when the window empties (lo > hi): the target is absent,
which LeetCode reports as -1.

Why overflow-safe: Python ints are arbitrary precision, so the classic
`mid = (lo + hi) // 2` cannot overflow here; in fixed-width languages you
would write `lo + (hi - lo) // 2` instead.

Complexity: O(log n) time — the window halves each iteration; O(1) space —
only three integer indices are kept.
"""
from __future__ import annotations


class Solution:
    def search(self, nums: list[int], target: int) -> int:
        lo, hi = 0, len(nums) - 1   # closed window; empty array -> hi = -1, loop skipped
        while lo <= hi:             # window still has candidates
            mid = (lo + hi) // 2    # midpoint of the current window
            if nums[mid] < target:
                lo = mid + 1       # target can only live strictly right of mid
            elif nums[mid] > target:
                hi = mid - 1       # ...or strictly left of mid
            else:
                return mid         # exact hit — this is the only success exit
        return -1                  # window empty: every index was ruled out
