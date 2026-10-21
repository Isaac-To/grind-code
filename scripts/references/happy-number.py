"""Reference solution — 202. Happy Number.

Approach: repeatedly replace n with the sum of the squares of its digits.
The iteration has only two possible fates: it reaches 1 (happy) or it falls
into a cycle (unhappy). Detect the cycle with Floyd's tortoise-and-hare:
advance a slow pointer one step and a fast pointer two steps per round; a
cycle makes them meet, reaching 1 makes the fast pointer hit 1 first.

Why it works (why a cycle is guaranteed at all): for any n with d digits,
the next value is at most 81*d, so values above 993 quickly drop and the
whole trajectory is confined to a finite set — a bounded sequence that
never repeats must eventually repeat, i.e. cycle or hit 1. Floyd's meeting
test needs O(1) space, unlike a visited-set solution.

Invariant: at the end of each loop, `slow` and `fast` hold values that are
both reachable from n, and neither has ever skipped past 1 unnoticed
(the fast pointer checks for 1 after every move).

Complexity: O(log n) per digit-square step (number of digits), with the
value capped at 243 after the first step, so effectively O(log n) time;
O(1) space.
"""
from __future__ import annotations


class Solution:
    def isHappy(self, n: int) -> bool:
        def next_value(v: int) -> int:
            total = 0
            while v > 0:
                v, digit = divmod(v, 10)   # pop the last decimal digit
                total += digit * digit    # accumulate its square
            return total

        slow = n
        fast = next_value(n)              # fast starts one step ahead
        while fast != 1 and slow != fast:
            slow = next_value(slow)               # one step
            fast = next_value(next_value(fast))   # two steps
        return fast == 1                  # met at 1 -> happy; met elsewhere -> cycle
