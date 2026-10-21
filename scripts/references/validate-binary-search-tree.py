"""Reference solution — 98. Validate Binary Search Tree.

Approach: recursion carrying an exclusive (lo, hi) interval. Every node's
value must lie strictly inside the bounds it inherits: left children get
(parent.val, hi), right children get (lo, parent.val).

Why plain "left < me < right" checks are WRONG: they miss violations deeper
down — e.g. node 5 in the right subtree of 10 but left-child chain under a
value 6. The interval carries ancestor constraints down, so a grandchild can
still be caught violating its grandparent's bound.

Invariant: check(node, lo, hi) is true exactly when the subtree rooted at
`node` is a valid BST whose every value lies strictly within (lo, hi). The
root starts with (-inf, +inf) so it imposes no artificial constraint;
Python floats give us those infinities directly.

Complexity: O(n) time — each node visited once; O(h) space for the
recursion stack.
"""
from __future__ import annotations


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def isValidBST(self, root: TreeNode | None) -> bool:
        def check(node: TreeNode | None, lo: float, hi: float) -> bool:
            if node is None:
                return True                 # empty subtree is vacuously valid
            if not (lo < node.val < hi):    # must beat BOTH ancestor bounds
                return False
            # Left subtree is bounded above by this value; right below by it.
            return (
                check(node.left, lo, node.val)
                and check(node.right, node.val, hi)
            )

        return check(root, float("-inf"), float("inf"))
