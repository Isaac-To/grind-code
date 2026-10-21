"""Reference solution — 322. Coin Change.

Approach: unbounded-knapsack style bottom-up DP. Let dp[a] = fewest coins
making amount a. For each amount a and each coin c with c <= a:
    dp[a] = min(dp[a], dp[a - c] + 1)
because an optimal solution for a ends with SOME last coin c, and before
that coin the remainder a-c was itself optimally paid.

Invariant: after processing amount a, dp[a] is the true minimum (or
infinity if a is unreachable): every candidate "last coin" is tried, and
dp[a-c] is already optimal by induction. dp[0] = 0 (pay nothing).

Amounts start at 1; dp[0] = 0 seeds the recurrence. Unreachable amounts
keep the sentinel `inf`, returned as -1 at the end.

Complexity: O(amount * len(coins)) time, O(amount) space.
"""
from __future__ import annotations


class Solution:
    def coinChange(self, coins: list[int], amount: int) -> int:
        INF = float("inf")
        # dp[a] = fewest coins for amount a; INF marks "unreachable so far"
        dp = [0] + [INF] * amount
        for a in range(1, amount + 1):
            for c in coins:
                if c <= a and dp[a - c] + 1 < dp[a]:
                    dp[a] = dp[a - c] + 1   # pay coin c last
        return -1 if dp[amount] == INF else dp[amount]
