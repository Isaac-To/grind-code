"""Reference solution — 138. Copy List with Random Pointer.

Approach: interleave-and-split (O(1) extra space, no hash map).
  1. Weave a clone C_i after each original node O_i:  O0 C0 O1 C1 ...
  2. Every clone's `random` is then reachable as
     `original.random.next` — the clone of whatever the original pointed to.
  3. Unzip the weave: originals re-link among themselves, clones likewise.

Invariant after step 1: for every node X in the original list, the clone
of X is X.next. Hence if O.random is R, the clone pair C.random is
R.next — the correct cloned target (None when R is None, because a
clone's .next of a trailing None... handled explicitly).

Complexity: O(n) time — three linear passes; O(1) space — the clones live
inside the existing list, no auxiliary map.
"""
from __future__ import annotations

from typing import Optional


class Node:
    def __init__(self, x, next=None, random=None):
        self.val = x
        self.next = next
        self.random = random


class Solution:
    def copyRandomList(self, head: 'Optional[Node]') -> 'Optional[Node]':
        if not head:
            return None

        # Pass 1: weave a clone after each original node.
        cur = head
        while cur:
            clone = Node(cur.val, cur.next)   # clone points at the ORIGINAL successor
            cur.next = clone                 # original now points at its clone
            cur = clone.next                 # jump past the clone to the next original

        # Pass 2: give each clone its random pointer.
        cur = head
        while cur:
            clone = cur.next                 # cur's clone (always exists after pass 1)
            clone.random = cur.random.next if cur.random else None
            cur = clone.next                 # advance to the next original

        # Pass 3: unzip into the original list and the cloned list.
        cur = head
        clone_head = head.next              # first clone — the answer's head
        while cur:
            clone = cur.next
            cur.next = clone.next           # restore the original's successor
            clone.next = clone.next.next if clone.next else None
            cur = cur.next
        return clone_head
