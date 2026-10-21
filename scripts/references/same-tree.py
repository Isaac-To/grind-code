"""Reference solution — 100. Same Tree.

Approach: synchronized recursion. Compare the two current nodes; if their
values match, demand that their left children are the same tree and their
right children are the same tree. Two nulls are the same (base case), one
null and one non-null are not.

Invariant: isSameTree(p, q) is true exactly when the two subtrees are
structurally identical with equal values at every corresponding position.
The recursion visits corresponding node pairs together, so any first
mismatch — a structural or value difference — is detected at that pair and
short-circuits via Python's `and` to False.

Complexity: O(min(m, n)) time — we stop at the first structural mismatch;
O(min(h_p, h_q)) space for the recursion stack.
"""
from __future__ import annotations


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def isSameTree(self, p: TreeNode | None, q: TreeNode | None) -> bool:
        # Both empty: identical by definition.
        if p is None and q is None:
            return True
        # Exactly one empty: structures differ.
        if p is None or q is None:
            return False
        # Values must match here, and recursively in both child pairs.
        return (
            p.val == q.val
            and self.isSameTree(p.left, q.left)
            and self.isSameTree(p.right, q.right)
        )
