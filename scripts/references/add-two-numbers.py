"""Reference solution — 2. Add Two Numbers.

Approach: simultaneous digit-by-digit addition with a carry. Because the
digits are stored least-significant first, the two numbers align at the
list heads — exactly like adding numbers on paper from the right.

Invariant: after processing position i, the result list holds the low i+1
digits of l1 + l2, and `carry` is 0 or 1 — the value that must be added
into position i+1. The loop continues while ANY input digit or a pending
carry remains, so the answer never loses its most significant digit.

Complexity: O(max(n, m)) time — one step per digit position;
O(max(n, m) + 1) space for the result list itself, O(1) auxiliary.
"""
from __future__ import annotations

from typing import Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def addTwoNumbers(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
        dummy = ListNode()          # sentinel: no special case for the first digit
        tail = dummy
        carry = 0                   # pending carry into the current position (0 or 1)
        while l1 or l2 or carry:    # a carry alone can create one extra digit (999+1)
            total = carry           # start from the carry of the previous position
            if l1:
                total += l1.val
                l1 = l1.next
            if l2:
                total += l2.val
                l2 = l2.next
            carry, digit = divmod(total, 10)   # carry is total // 10 (always 0 or 1)
            tail.next = ListNode(digit)        # append the position's digit
            tail = tail.next
        return dummy.next
