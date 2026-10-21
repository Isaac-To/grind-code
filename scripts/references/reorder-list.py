"""Reference solution — 143. Reorder List.

Approach: three classic phases, all in place.
  1. Find the middle with slow/fast pointers (slow ends on the first
     middle node for even lengths).
  2. Reverse the second half.
  3. Interleave: alternately take one node from the front half and one
     from the reversed back half, until the back half is exhausted.

Invariant after phase 2: `first` leads nodes 0..mid-1 in order and
`second` leads nodes mid..end in reverse order — so peeling one node from
each alternately yields L0, Ln, L1, Ln-1, ... exactly as required.

Complexity: O(n) time — each node is visited a constant number of times;
O(1) space — only pointers, nodes are rewired in place.
"""
from __future__ import annotations

from typing import Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def reorderList(self, head: Optional[ListNode]) -> None:
        if not head or not head.next:
            return                   # 0 or 1 nodes: already in the required form

        # Phase 1: slow lands on the first middle node.
        slow = fast = head
        while fast.next and fast.next.next:
            slow = slow.next
            fast = fast.next.next

        # Phase 2: reverse the half after `slow` (standard 3-pointer flip).
        prev, cur = None, slow.next
        slow.next = None             # cut the list in two: front half ends at slow
        while cur:
            nxt = cur.next
            cur.next = prev
            prev = cur
            cur = nxt
        second = prev                # head of the reversed back half (or None)

        # Phase 3: interleave front (from head) and back (from second).
        first = head
        while second:                # back half is never longer than the front
            tmp_first, tmp_second = first.next, second.next
            first.next = second     # front node -> back node
            second.next = tmp_first # back node -> next front node
            first, second = tmp_first, tmp_second
        # `head` still points at node 0 — the reordering is fully in place
