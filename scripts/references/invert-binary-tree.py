"""Reference solution — 226. Invert Binary Tree.

Approach: recursive swap-and-recurse. For every node, swap its two children,
then invert each subtree. A null node is its own inverse, so the recursion
bottoms out without any special casing.

Invariant: when invert(node) returns, the subtree rooted at `node` is the
mirror image of what it was on entry — left and right subtrees have been
recursively inverted and then exchanged, and a mirrored mirror is the
original, so the composition is a full mirror. Processing each node exactly
once makes this a total inversion, not a partial one.

Complexity: O(n) time — every node is visited once; O(h) space for the
recursion stack, where h is the tree height (O(n) worst case for a chain,
O(log n) for a balanced tree).
"""
from __future__ import annotations


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def invertTree(self, root: TreeNode | None) -> TreeNode | None:
        if root is None:            # empty subtree: nothing to mirror
            return None
        # Swap children first, then invert the (already swapped) subtrees.
        root.left, root.right = root.right, root.left
        self.invertTree(root.left)   # mirror the new left subtree
        self.invertTree(root.right)  # mirror the new right subtree
        return root                  # the same node object, now inverted
