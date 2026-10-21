"""Reference solution — 543. Diameter of Binary Tree.

Approach: post-order recursion that computes each node's *height* (edges to
its deepest leaf) and, along the way, updates a running answer with the best
path that *bends* at that node: left_height + right_height edges.

Invariant: when height(node) returns, `best` already holds the maximum path
length (in edges) over every pair of nodes whose connecting path has its
highest point at or below `node`. A bend-path through `node` is exactly
height(left) + height(right) edges, and any path has its highest point
somewhere, so scanning all bend candidates covers all paths.

Why heights are "edges" (null -> 0, leaf -> 0): the bend formula then counts
the two downward legs without double-counting the bend node itself.

Complexity: O(n) time — each node visited once; O(h) space for the recursion
stack.
"""
from __future__ import annotations


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def diameterOfBinaryTree(self, root: Optional[TreeNode]) -> int:  # noqa: F821
        best = 0  # longest path (edges) seen so far, anywhere in the tree

        def height(node: Optional[TreeNode]) -> int:  # noqa: F821
            nonlocal best
            if node is None:
                return 0                      # empty subtree: 0 edges to a leaf
            left = height(node.left)          # height of left subtree in edges
            right = height(node.right)        # height of right subtree in edges
            # Best path bending here: down-left leg + down-right leg.
            best = max(best, left + right)
            # This node extends its best leg by one edge going up.
            return 1 + max(left, right)

        height(root)
        return best
