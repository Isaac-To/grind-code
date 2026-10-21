"""Reference solution — 309. Best Time to Buy and Sell Stock with Cooldown.

Approach: state-machine dynamic programming. On any day you are in exactly
one of three states:
  hold  — currently holding a share
  sold  — sold a share *today* (forces a cooldown tomorrow)
  rest  — free to act (no share, no fresh sale)

Transitions at price p:
  hold[i] = max(hold[i-1], rest[i-1] - p)   keep holding, or buy from rest
  sold[i] = hold[i-1] + p                    sell the held share today
  rest[i] = max(rest[i-1], sold[i-1])        stay idle, or finish cooldown

Invariant: each state's value is the maximum cash achievable while ending
day i in that state. Every legal schedule is a path through these states,
so the answer is the best cash with no share left at the end:
max(rest[-1], sold[-1]) — holding on the last day is never optimal.

Initialization: hold = -infinity (impossible to hold before buying),
sold = -infinity (nothing to sell on day 0), rest = 0 (do nothing).

Complexity: O(n) time, O(1) space — three rolling scalars.
"""
from __future__ import annotations


class Solution:
    def maxProfit(self, prices: list[int]) -> int:
        hold = float("-inf")   # holding a share; impossible before day 0
        sold = float("-inf")   # sold today; impossible on day 0
        rest = 0               # idle and free to buy
        for p in prices:
            hold, sold, rest = (
                max(hold, rest - p),   # buy today (only from rest) or keep
                hold + p,              # sell today's held share at price p
                max(rest, sold),       # stay idle or just finished cooldown
            )
            # Tuple assignment uses the *old* values on the right — exactly
            # the day-(i-1) states every transition needs.
        return max(rest, sold)   # never optimal to end still holding
