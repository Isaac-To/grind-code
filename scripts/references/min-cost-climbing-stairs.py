"""Reference solution — 746. Min Cost Climbing Stairs.

Approach: you may start at index 0 or 1 and, from step i, pay cost[i] to
jump to i+1 or i+2. Define dp[i] = cheapest total cost to *stand* on step i.
Then dp[i] = min(dp[i-1] + cost[i-1], dp[i-2] + cost[i-2]): the last move
onto step i came from i-1 or i-2, paying that step's cost.

Invariant: dp[i] is the minimum cost to reach step i, and reaching step i
via its two predecessors exhausts all possibilities. The answer is dp[n]
(the "top", one past the last step), since you can finish from step n-1 or
n-2; dp[n] already takes the cheaper of exactly those two.

Base cases: dp[0] = dp[1] = 0 — starting on either allowed step is free.

Complexity: O(n) time, O(1) space (only the last two dp values are kept).
"""
from __future__ import annotations


class Solution:
    def minCostClimbingStairs(self, cost: list[int]) -> int:
        # dp_prev = dp[i-1], dp_curr = dp[i]; both start free.
        dp_prev, dp_curr = 0, 0
        for i in range(2, len(cost) + 1):          # climb up to step n (the top)
            dp_prev, dp_curr = dp_curr, min(
                dp_curr + cost[i - 1],   # last move: single step from i-1
                dp_prev + cost[i - 2],   # last move: double step from i-2
            )
        return dp_curr
