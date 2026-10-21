"""Reference solution — 416. Partition Equal Subset Sum.

Approach: a valid split exists iff some subset sums to total/2 (the rest is
the complement). If total is odd, no split exists. Otherwise run a 0/1
knapsack reachability DP over the target t = total // 2: `reachable` is a
boolean bitmask where bit a is set iff some subset of the numbers seen so
far sums to a.

Bit-trick update: ORing `mask << num` into the mask adds "take num" to
every previously reachable sum; keeping the old mask covers "skip num".
Processing each number once makes it a true 0/1 knapsack (each element used
at most once — hence the per-number snapshot via shifting before OR).

Invariant: after processing numbers n1..nk, bit a of `reachable` is set iff
some subset of {n1..nk} sums to a. The answer is bit t.

Complexity: O(n * total/32) time via Python's big-int bitwise ops, O(total)
space for the single integer mask.
"""
from __future__ import annotations


class Solution:
    def canPartition(self, nums: list[int]) -> bool:
        total = sum(nums)
        if total % 2:                 # odd total can never split evenly
            return False
        target = total // 2
        reachable = 1                 # bit 0 set: empty subset sums to 0
        for num in nums:
            # every reachable sum a also yields a + num (skip case is kept by OR)
            reachable |= reachable << num
        return (reachable >> target) & 1 == 1
