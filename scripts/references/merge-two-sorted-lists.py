"""Reference solution — 21. Merge Two Sorted Lists.

Approach: dummy-head splicing. A sentinel `dummy` node anchors the output
so the first node needs no special case; `tail` always points at the last
node already spliced. Repeatedly link the smaller front node of the two
lists onto `tail`, advancing that list. Finally attach whatever remains.

Invariant: at every step the chain starting at `dummy` is sorted and
contains the smallest (len1 + len2 - remaining) values of both inputs;
the next value appended is the minimum of the two current fronts, so
sortedness is preserved.

Complexity: O(n + m) time — each node is linked exactly once;
O(1) space — existing nodes are reused, no new allocations.
"""
from __future__ import annotations

from typing import Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def mergeTwoLists(self, list1: Optional[ListNode], list2: Optional[ListNode]) -> Optional[ListNode]:
        dummy = ListNode()          # sentinel: removes "empty result" special case
        tail = dummy                # last node already spliced into the result
        while list1 and list2:      # both lists still have nodes
            if list1.val <= list2.val:
                tail.next = list1   # take from list1 (<= keeps the merge stable)
                list1 = list1.next
            else:
                tail.next = list2   # take from list2
                list2 = list2.next
            tail = tail.next        # the appended node is the new tail
        tail.next = list1 or list2  # one list is exhausted: splice the other whole
        return dummy.next           # first real node (None if both inputs were empty)
