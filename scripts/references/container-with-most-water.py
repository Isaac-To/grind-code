"""Reference solution — 11. Container With Most Water.

Approach: two pointers at the two ends, always moving the pointer at
the *shorter* line inward, tracking the best area seen.

Invariant: the optimal pair is never skipped. Consider the pair
(lo, hi) with height[lo] <= height[hi]: its area is height[lo] *
(hi - lo), and height[lo] can never do better — paired with any
other interior index j, the width is smaller and the effective
height is still capped at height[lo]. So height[lo] is now useless
and can be discarded. The symmetric argument applies when the right
line is shorter. Hence each discard is safe and one of the remaining
pairs must be the optimum.

Area formula: min(h[lo], h[hi]) * (hi - lo) — water is limited by
the shorter line and the distance between them.

Complexity: O(n) time — each iteration removes one candidate index;
O(1) space — two indices and the running best.
"""
from __future__ import annotations


class Solution:
    def maxArea(self, height: list[int]) -> int:
        lo, hi = 0, len(height) - 1   # widest container first
        best = 0                      # max area found so far
        while lo < hi:
            # Water level is capped by the shorter of the two lines.
            width = hi - lo
            area = min(height[lo], height[hi]) * width
            if area > best:
                best = area           # new record — remember it
            # Discard the shorter line: it can never form a better
            # container with any remaining index than the one just tried.
            if height[lo] < height[hi]:
                lo += 1
            else:
                hi -= 1
        return best
