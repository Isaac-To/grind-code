"""Reference solution — 25. Reverse Nodes in k-Group.

Approach: iterate group by group. For each group first CHECK that k nodes
remain (a short tail is left untouched — the problem's key rule), then
reverse those k nodes in place with the standard 3-pointer flip, and
stitch the flipped group between the previous group's end (`prev_group`)
and the next group's start.

Invariant: `prev_group` is always the last node of the already-fixed
prefix, and `group_start` is the first node of the next candidate group.
After flipping, prefix + reversed group is correct and prev_group
advances to the group's old head (its new tail).

Complexity: O(n) time — each node is inspected and flipped O(1) times;
O(1) space — pointers only, no recursion stack.
"""
from __future__ import annotations

from typing import Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def reverseKGroup(self, head: Optional[ListNode], k: int) -> Optional[ListNode]:
        dummy = ListNode(0, head)   # sentinel: the head group needs no special case
        prev_group = dummy          # last node of the already-processed prefix

        while True:
            # Check that a full group of k nodes exists; if not, we are done
            # and the short tail must stay in its ORIGINAL order.
            node = prev_group
            for _ in range(k):
                node = node.next
                if node is None:
                    return dummy.next

            group_start = prev_group.next   # first node of the group
            nxt_group = node.next           # first node AFTER the group

            # Standard in-place reversal of the k nodes.
            prev, cur = nxt_group, group_start
            for _ in range(k):      # exactly k flips
                cur.next, prev, cur = prev, cur, cur.next
            # `prev` is now the group's new head (old k-th node).

            prev_group.next = prev          # stitch: prefix -> reversed group
            group_start.next = nxt_group     # stitch: group tail -> next group
            prev_group = group_start         # group's old head is the new prefix end
