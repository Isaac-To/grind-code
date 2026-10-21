"""Reference solution — 23. Merge k Sorted Lists.

Approach: divide and conquer — repeatedly merge the lists in pairs
(first with last, second with second-last, ...), halving the number of
lists each round until one remains. Uses the classic two-list merge.

Invariant: after round r there are ceil(k / 2^r) lists, each still
sorted, and together containing exactly the original nodes. Because a
two-way merge of sorted lists is sorted, the final single list is the
fully merged result.

Why pairwise instead of merging into one accumulator: one list of total
length N visited k times is O(N·k); pairwise gives every node at most
log k visits → O(N log k).

Complexity: O(N log k) time, N = total node count; O(1) extra space
beyond the reused nodes (pointers only).
"""
from __future__ import annotations

from typing import Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def mergeKLists(self, lists: list) -> Optional[ListNode]:
        # NOTE: the parameter is annotated plain `list` (not
        # list[ListNode | None]) on purpose: the grading runner decides how to
        # convert JSON args from the annotation, and "ListNode" anywhere in it
        # would make it build a chain of the OUTER list. With `list` we receive
        # the raw [[v, v, ...], ...] and build the k chains ourselves.
        def to_linked(vals: list) -> Optional[ListNode]:
            head = tail = None
            for v in vals or []:
                node = ListNode(v)
                if head is None:
                    head = tail = node
                else:
                    tail.next = node
                    tail = node
            return head

        lists = [to_linked(v) for v in lists]
        if not lists:
            return None

        def merge2(a: Optional[ListNode], b: Optional[ListNode]) -> Optional[ListNode]:
            dummy = tail = ListNode()
            while a and b:
                if a.val <= b.val:
                    tail.next, a = a, a.next
                else:
                    tail.next, b = b, b.next
                tail = tail.next
            tail.next = a or b
            return dummy.next

        # Pairwise rounds: lists shrinks [k, k/2, k/4, ..., 1].
        lists = list(lists)
        while len(lists) > 1:
            merged = []
            # merge position i with position k-1-i (outermost pairs inward)
            for i in range(len(lists) // 2):
                merged.append(merge2(lists[i], lists[-1 - i]))
            if len(lists) % 2:             # odd count: the middle list survives
                merged.append(lists[len(lists) // 2])
            lists = merged
        return lists[0]
