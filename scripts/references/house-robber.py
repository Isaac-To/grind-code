"""Reference solution — 198. House Robber.

Approach: choosing to rob house i forbids robbing its neighbour, so the
best loot after considering houses 0..i is
    best(i) = max(best(i-1),           # skip house i
                 best(i-2) + nums[i]) # rob house i, loot was frozen at i-2

Invariant: after iteration i, `robbed` holds best(i-1) with house i-1 NOT
available as a neighbour constraint... more precisely: `skip` = best(i-2)
and `robbed` = best(i-1). Updating `skip, robbed = robbed, max(robbed,
skip + nums[i])` advances both one house forward while preserving the
invariant — no choice of a valid subset is ever lost.

Complexity: O(n) time, O(1) space.
"""
from __future__ import annotations


class Solution:
    def rob(self, nums: list[int]) -> int:
        skip, robbed = 0, 0        # best loot with i-2 / i-1 as last considered
        for money in nums:
            # either keep the plan that skipped this house, or rob it on top
            # of the best plan that ended two houses back
            skip, robbed = robbed, max(robbed, skip + money)
        return robbed
