"""Reference solution — 134. Gas Station.

Approach: one greedy pass. Two facts do all the work:

1. If total gas >= total cost, a valid start exists (and the problem
   guarantees it is unique). If total < 0, no start works: return -1.
2. If you start at `start` and the running tank first goes negative when you
   arrive at station i, then NO station in [start, i] can be a valid start.
   Why: gas tanks are non-negative throughout [start, i), so re-starting at
   any later station j in that range only gives you *less* fuel at i than
   continuing from `start` did. Hence the next candidate is i + 1.

Invariant: after the loop, `start` is the only station not ruled out by
fact 2, and fact 1 guarantees it works.

Complexity: O(n) time, O(1) space.
"""
from __future__ import annotations


class Solution:
    def canCompleteCircuit(self, gas: list[int], cost: list[int]) -> int:
        total = 0            # overall gas surplus: decides existence
        tank = 0             # fuel since the current candidate start
        start = 0
        for i in range(len(gas)):
            total += gas[i] - cost[i]
            tank += gas[i] - cost[i]
            if tank < 0:     # cannot pass station i from `start`: rule out [start, i]
                start = i + 1
                tank = 0
        return start if total >= 0 else -1
