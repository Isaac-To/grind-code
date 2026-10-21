"""Reference solution — 121. Best Time to Buy and Sell Stock.

Approach: single left-to-right sweep keeping the cheapest price seen so far.
For each day, the best trade ending with a sale on that day is
`prices[i] - min_price_so_far`; the global answer is the max of these.

Invariant: when we visit index i, `min_price` holds the minimum of
prices[0..i-1] (updated after the profit check). Therefore
`prices[i] - min_price` is always the profit of a legal trade (buy strictly
before day i), and taking the running max over all i considers every possible
selling day — so no profitable single trade can be missed.

If prices only fall, every candidate profit is negative and we keep 0
(no transaction), matching the problem's requirement.

Complexity: O(n) time — one pass; O(1) space — two scalars.
"""
from __future__ import annotations


class Solution:
    def maxProfit(self, prices: list[int]) -> int:
        min_price = prices[0]  # cheapest buy price seen so far
        best = 0               # best profit found; 0 = "no transaction"
        for price in prices[1:]:
            # Profit if we sell today after buying at the cheapest earlier day.
            # Compare before updating min_price so the buy is strictly in the past.
            best = max(best, price - min_price)
            min_price = min(min_price, price)  # extend the prefix minimum
        return best
