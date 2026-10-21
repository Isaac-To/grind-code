"""Reference solution — 518. Coin Change II.

Approach: unbounded-knapsack counting with 1-D dynamic programming.
dp[a] = number of multisets (combinations) of the coins processed so far
that sum to a.

Process ONE coin at a time, and for each coin sweep a upward:
    for coin in coins:
        for a in range(coin, amount + 1):
            dp[a] += dp[a - coin]

Invariant (the heart of correctness): after processing coins[:k], dp[a]
counts the combinations of amount a using ONLY those k coins. Adding a
(k+1)-th coin, each dp[a - coin] already excludes it, so
"dp[a] + dp[a-coin]" adds combinations that use the new coin at least once
— without double counting, and never mixing orderings.

Why ascending order: unlike 0322-style minimization or permutation
counting, the coin sits outside the amount loop conceptually — the
coin-first loop order makes {1,2} and {2,1} the SAME combination, which is
what "combinations" demands. (Swapping the loops would count ordered
sequences instead.)

Base case: dp[0] = 1 — one way to make 0: use no coins.

Complexity: O(amount * len(coins)) time, O(amount) space.
"""
from __future__ import annotations


class Solution:
    def change(self, amount: int, coins: list[int]) -> int:
        dp = [1] + [0] * amount          # dp[0] = 1: empty combination
        for coin in coins:               # add one coin denomination at a time
            for a in range(coin, amount + 1):   # ascending: coin reusable
                dp[a] += dp[a - coin]    # combos using `coin` at least once
        return dp[amount]
