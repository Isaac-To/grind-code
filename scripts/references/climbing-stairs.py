"""Reference solution — 70. Climbing Stairs.

Approach: at any step k you arrived either from step k-1 (a 1-climb) or from
step k-2 (a 2-climb), so the number of distinct ways to reach step k is
ways(k) = ways(k-1) + ways(k-2) — the Fibonacci recurrence, with base cases
ways(1) = 1 (one single climb) and ways(2) = 2 (1+1 or 2).

Invariant: after processing step k, `prev` holds ways(k-1) and `curr` holds
ways(k). The update `prev, curr = curr, prev + curr` shifts that window one
step forward while the identity ways(k) = ways(k-1) + ways(k-2) holds.

We never need the whole table — only the last two values — so two rolling
variables replace the O(n) array.

Complexity: O(n) time, O(1) space.
"""
from __future__ import annotations


class Solution:
    def climbStairs(self, n: int) -> int:
        prev, curr = 1, 1          # ways(0)=1 (stay put), ways(1)=1
        for _ in range(n - 1):     # advance the window from step 1 to step n
            prev, curr = curr, prev + curr
        return curr                # ways(n); also correct for n == 1
