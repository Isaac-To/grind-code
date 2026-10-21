"""Reference solution — 141. Linked List Cycle.

Approach: Floyd's tortoise and hare — two pointers race down the list, the
slow one moving one node per step, the fast one two. If the list has no
cycle, the fast pointer runs off the end and we report False.

Why it works: inside a cycle the gap between the two pointers changes by
±1 each step (fast gains one on slow per iteration, modulo the cycle
length), so it is impossible for them to hop over each other without
landing on the same node: the gap must eventually hit exactly 0. Outside
a cycle the fast pointer simply reaches the None tail first.

Why not a visited set: hashing is O(n) extra memory; the two-pointer race
uses O(1) — the interview answer LeetCode is probing for.

Complexity: O(n) time, O(1) space.
"""
from __future__ import annotations

from typing import Optional


class ListNode:
    def __init__(self, val: int = 0, next: "Optional[ListNode]" = None):
        self.val = val
        self.next = next


class Solution:
    def hasCycle(self, head: Optional[ListNode]) -> bool:
        slow = fast = head          # both start at the gate
        while fast and fast.next:   # fast can bail early on odd/even tails
            slow = slow.next        # one hop
            fast = fast.next.next   # two hops — crashes to None off a list's end
            if slow is fast:        # identity, not value: same node revisited
                return True
        return False                # fast fell off: the list terminates
