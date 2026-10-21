"""Reference solution — 206. Reverse Linked List.

Approach: iterative three-pointer reversal. Walk the list once, flipping
each node's `next` pointer to point backwards. `prev` holds the already
reversed prefix, `cur` the node being flipped, `nxt` saves the rest of the
list before we overwrite `cur.next`.

Invariant: after processing node `cur`, `prev` is the head of a correctly
reversed chain containing exactly the nodes visited so far, and `nxt`
still leads to all unvisited nodes. When `cur` becomes None every node has
been flipped, so `prev` is the new head.

Why it works: each original edge (cur -> nxt) is replaced by (cur -> prev)
exactly once; no node is lost or duplicated, and the traversal order is
the original one, so the result is the exact reverse.

Complexity: O(n) time — one pass; O(1) space — three pointers only.
"""
from __future__ import annotations

from typing import Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def reverseList(self, head: Optional[ListNode]) -> Optional[ListNode]:
        prev = None                    # head of the reversed prefix (empty at start)
        cur = head                     # first node not yet flipped
        while cur:                     # stop after the last node is flipped
            nxt = cur.next             # save the rest before breaking the link
            cur.next = prev            # flip: point backwards instead of forwards
            prev = cur                 # prefix grew by one node
            cur = nxt                  # advance along the ORIGINAL order
        return prev                    # cur is None -> prev is the new head
