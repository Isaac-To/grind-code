"""Reference solution — 55. Jump Game.

Approach: greedy reachability sweep. Walk through the array keeping `reach`,
the farthest index known to be reachable.

Invariant: every index <= reach is reachable (indices between i and reach are
reachable because from any position you can jump any length up to its value,
which includes the lengths used to reach `reach` itself).

At index i we can jump to i + nums[i]. If i > reach, there is a gap that no
earlier jump could cross — return False. Otherwise extend
reach = max(reach, i + nums[i]); if reach covers the last index we're done.

Complexity: O(n) time, O(1) space.
"""
from __future__ import annotations


class Solution:
    def canJump(self, nums: list[int]) -> bool:
        last = len(nums) - 1
        reach = 0                     # farthest index proven reachable so far
        for i, jump in enumerate(nums):
            if i > reach:              # gap: no prior jump lands on or past i
                return False
            reach = max(reach, i + jump)
            if reach >= last:          # last index already reachable
                return True
        return True                    # len >= 1 and loop covered index 0
