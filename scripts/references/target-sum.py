"""Reference solution — 494. Target Sum.

Approach: restate as a subset-sum count, then count with dynamic
programming over reachable sums.

Key transformation: choose a sign for every number. Let P be the subset
given '+' and N the subset given '-'. Then
    sum(P) - sum(N) = target
    sum(P) + sum(N) = total      (every number is in one subset)
Adding:  2*sum(P) = total + target, so we must count subsets P with
    sum(P) = (total + target) / 2
Impossible immediately if total + target is odd or negative.

Counting: dp[s] = number of subsets (of the numbers seen so far) whose sum
is s. Process numbers one at a time, sweeping s DOWNWARD so each number is
used at most once (01-knapsack style):
    for x in nums:
        for s in range(cap, x - 1, -1):
            dp[s] += dp[s - x]

Invariant: after k numbers, dp[s] counts subsets of nums[:k] summing to s.
The downward sweep guarantees dp[s - x] still refers to the state BEFORE
x was considered, so no subset uses x twice.

Base case: dp[0] = 1 (the empty subset sums to 0).

Complexity: O(n * range) time, O(range) space where range = total + |target|.
"""
from __future__ import annotations


class Solution:
    def findTargetSumWays(self, nums: list[int], target: int) -> int:
        total = sum(nums)
        # sum(P) must be this exact non-negative integer:
        goal = (total + target) / 2
        # Odd or negative goal -> no integer subset can satisfy the equation.
        if goal != int(goal) or goal < 0:
            return 0
        cap = int(goal)
        dp = [1] + [0] * cap            # empty subset is the one way to sum 0
        for x in nums:                 # one number at a time (01-knapsack)
            for s in range(cap, x - 1, -1):   # descending: use x at most once
                dp[s] += dp[s - x]      # every old subset summing s-x gains x
        return dp[cap]
