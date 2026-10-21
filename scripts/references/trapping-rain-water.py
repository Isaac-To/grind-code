"""Reference solution — 42. Trapping Rain Water.

Approach: two pointers from both ends, tracking the tallest wall seen
so far on each side (left_max, right_max). At each step, advance the
pointer on the side whose best wall is shorter: water above that
pointer is exactly its side's best-wall height minus the ground,
because the *other* side is guaranteed to have a wall at least that
tall somewhere (its best is larger), so the effective lid is
left_max/right_max.

Invariant: when left_max <= right_max, the water level above
position `lo` is exactly left_max - height[lo] — independent of the
unknown walls to the right, because right_max already certifies a
wall >= left_max exists there, and water cannot rise above the
smaller of the two side maxima. The symmetric claim holds for the
right pointer. So every unit of water is counted exactly once, when
its own column is the pointer being consumed.

Complexity: O(n) time — each pointer moves monotonically inward;
O(1) space — four scalars.
"""
from __future__ import annotations


class Solution:
    def trap(self, height: list[int]) -> int:
        lo, hi = 0, len(height) - 1   # scan from both ends
        left_max = right_max = 0      # tallest wall strictly available per side
        water = 0                     # total units trapped
        while lo < hi:
            if height[lo] < height[hi]:
                # Left side is the limiting one: lid above `lo` is left_max.
                if height[lo] >= left_max:
                    left_max = height[lo]   # new left wall, no water here
                else:
                    water += left_max - height[lo]  # fill up to left_max
                lo += 1
            else:
                # Mirror image on the right side.
                if height[hi] >= right_max:
                    right_max = height[hi]
                else:
                    water += right_max - height[hi]
                hi -= 1
        return water
