"""Reference solution — 19. Remove Nth Node From End of List.

Approach: two pointers with a `n`-node gap. Send `fast` n nodes ahead,
then move both until `fast` falls off the end. At that moment `slow` sits
exactly one node BEFORE the victim, so `slow.next` can be unlinked.

Invariant: distance(fast, slow) == n throughout the synchronized walk, so
when fast is None (past the end), slow is at position len - n - 1 — the
predecessor of the n-th-from-last node. A dummy head makes removing the
original head (n == len) the same as removing any other node.

Complexity: O(n) time — one pass; O(1) space — two pointers plus dummy.
"""
from __future__ import annotations

from typing import Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def removeNthFromEnd(self, head: Optional[ListNode], n: int) -> Optional[ListNode]:
        dummy = ListNode(0, head)   # sentinel: head removal needs no special case
        slow = fast = dummy
        for _ in range(n):          # open a gap of exactly n nodes
            fast = fast.next
        while fast.next:            # advance until fast is ON the last node
            slow = slow.next
            fast = fast.next
        slow.next = slow.next.next  # unlink the victim (guaranteed to exist)
        return dummy.next           # real head (None if the list is now empty)
