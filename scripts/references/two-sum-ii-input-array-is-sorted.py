"""Reference solution — 167. Two Sum II - Input Array Is Sorted.

Approach: two pointers at the ends of the sorted array. If the ends
sum too high, the right value can never participate in the answer
(it pairs even larger with anything left of `right` that we have not
ruled out), so shrink from the right; if too low, the left value is
useless, so shrink from the left.

Invariant: the answer pair, if it exists, always lies inside the
current window [lo, hi]. Each step discards one endpoint with a
proof-by-sortedness argument, so the window shrinks by one each
iteration and the unique solution is found in at most n-1 steps.
Because the problem guarantees exactly one solution, no miss check
is needed.

Return convention: 1-based indices, smallest first — exactly what
the two-pointer scan produces.

Complexity: O(n) time — one pass, each element visited once;
O(1) space — just the two indices.
"""
from __future__ import annotations


class Solution:
    def twoSum(self, numbers: list[int], target: int) -> list[int]:
        lo, hi = 0, len(numbers) - 1  # closed window; answer inside it
        while lo < hi:               # at least two candidates remain
            total = numbers[lo] + numbers[hi]
            if total == target:
                return [lo + 1, hi + 1]  # hit: convert to 1-based indices
            if total < target:
                lo += 1             # sum too small: drop the smallest value
            else:
                hi -= 1             # sum too large: drop the largest value
        return []                   # unreachable per problem guarantee
