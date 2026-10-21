"""Reference solution — 110. Balanced Binary Tree.

Approach: bottom-up height computation that short-circuits on imbalance.
check(node) returns the subtree height, or -1 as a sentinel meaning "this
subtree is already unbalanced". The moment any subtree reports -1, the
failure propagates up unchanged — no work is redone.

Invariant: a subtree is balanced iff its two children's subtrees are both
balanced AND their heights differ by at most 1. Encoding "unbalanced" as -1
lets one integer carry both pieces of information, so each node is examined
exactly once (O(n), versus the naive top-down O(n log n) or O(n^2)).

Complexity: O(n) time; O(h) space for the recursion stack.
"""
from __future__ import annotations


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def isBalanced(self, root: TreeNode | None) -> bool:
        def check(node: TreeNode | None) -> int:
            if node is None:
                return 0                       # empty subtree: height 0, balanced
            left = check(node.left)            # -1 means "already unbalanced below"
            if left == -1:
                return -1
            right = check(node.right)
            if right == -1:
                return -1
            if abs(left - right) > 1:          # imbalance exactly at this node
                return -1
            return 1 + max(left, right)        # genuine height of this subtree

        return check(root) != -1
