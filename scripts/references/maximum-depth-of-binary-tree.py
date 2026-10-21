"""Reference solution — 104. Maximum Depth of Binary Tree.

Approach: post-order recursion. The depth of a tree is 1 (for the root) plus
the depth of its deeper child. A null tree has depth 0, which anchors the
recursion.

Invariant: maxDepth(node) returns the number of nodes on the longest
root-to-leaf path within the subtree rooted at `node`. Each call trusts its
children's answers and only adds its own single node on top, so by induction
on subtree height the returned value is exact.

Complexity: O(n) time — every node is visited once; O(h) space for the
recursion stack (h = tree height, up to n for a skewed tree).
"""
from __future__ import annotations


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def maxDepth(self, root: TreeNode | None) -> int:
        if root is None:                      # empty subtree contributes no nodes
            return 0
        # Longest path goes through whichever child subtree is deeper.
        return 1 + max(self.maxDepth(root.left), self.maxDepth(root.right))
