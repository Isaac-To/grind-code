"""Reference solution — 287. Find the Duplicate Number.

Approach: Floyd's tortoise-and-hare on an implicit functional graph.
Treat the array as a function f(i) = nums[i]: since every value is in
[1, n] and index 0 is nobody's target, following i -> nums[i] walks a
"rho" shape — a tail leading into a cycle, and the cycle's entry IS the
duplicate value (two different indices i, j with nums[i] == nums[j] ==
the entry both point there, forming the loop).

Phase 1: slow moves 1 step, fast 2 steps from index 0; they must meet
inside the cycle. Phase 2: reset one pointer to the start and advance
both by 1 — they meet exactly at the cycle entry, i.e. the duplicate.

Why phase 2 works (the classic invariant): if the tail (start → entry)
has length t and the meeting point is s steps into the cycle, then slow
travelled t + s while fast travelled 2(t + s); the difference t + s is a
multiple of the cycle length L. Moving t more steps from the meeting
point lands on the entry, and moving t steps from the start also lands
on the entry — hence the two pointers coincide there.

Respects the constraints: the array is never modified and only two
integer pointers are used.

Complexity: O(n) time — phase 1 is at most ~t + 2L steps, phase 2 t;
O(1) space.
"""
from __future__ import annotations


class Solution:
    def findDuplicate(self, nums: list[int]) -> int:
        slow = fast = 0
        # Phase 1: detect the cycle (they meet somewhere inside it).
        while True:
            slow = nums[slow]           # one hop
            fast = nums[nums[fast]]     # two hops
            if slow == fast:
                break
        # Phase 2: find the entry — pointer arithmetic from the meeting point.
        slow = 0                       # restart at the head of the rho
        while slow != fast:
            slow = nums[slow]           # both now move at the SAME speed
            fast = nums[fast]
        return slow                     # the shared entry index == the duplicate value
