"""Reference solution — 45. Jump Game II.

Approach: implicit BFS over jump levels. The set of indices reachable in
`jumps` steps is an interval [l, r] (intervals only grow as jumps increase,
since jumps are flexible in length). We sweep once, tracking:
  - `cur_end`:   right edge of the interval reachable with `jumps` steps
  - `next_end`:  right edge reachable with `jumps + 1` steps (one more jump
                 from anything in the current interval)

Invariant: while scanning index i < cur_end (i.e. i is reachable in `jumps`
steps), next_end = max(next_end, i + nums[i]) is the farthest index reachable
in jumps+1 steps. When the scan pointer passes cur_end, we must spend one
more jump to go further: jumps += 1, cur_end = next_end.

Stop once cur_end >= n-1 — the last index is inside the current interval.
The `if i == n-1` guard handles the trivial n == 1 case (0 jumps).

Complexity: O(n) time, O(1) space.
"""
from __future__ import annotations


class Solution:
    def jump(self, nums: list[int]) -> int:
        n = len(nums)
        jumps = 0
        cur_end = 0        # farthest index reachable with `jumps` steps
        next_end = 0       # farthest index reachable with one more step
        for i in range(n - 1):       # no need to jump *from* the last index
            next_end = max(next_end, i + nums[i])
            if i == cur_end:         # exhausted the current level: step up
                jumps += 1
                cur_end = next_end
                if cur_end >= n - 1:
                    break
        return jumps
