"""Reference solution — 124. Binary Tree Maximum Path Sum.

Approach: post-order recursion computing, for each node, the best *gain* of
a path that starts at that node and runs downward into one subtree (0 if
both children are losses, since a path need not extend). While doing so,
update a global answer with the best *full* path bending at that node:
node.val + left_gain + right_gain.

Invariant: gain(node) is the maximum sum of any path that starts at `node`
and continues downward into at most one child — never negative, because
extending into a losing subtree can be skipped (an empty extension has sum
0, but the node itself is always counted, matching "non-empty path"). The
best path anywhere has its highest point at some node, and there it is
exactly node.val + gain(left) + gain(right); tracking all bend candidates
covers every path.

Negative values are the trap: single negative nodes can be the answer
(bundled test [-10,9,20,...] shows answers ignoring the root), hence the
initialization to -infinity rather than 0.

Complexity: O(n) time — each node visited once; O(h) space recursion stack.
"""
from __future__ import annotations


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def maxPathSum(self, root: TreeNode | None) -> int:
        best = float("-inf")  # best complete-path sum seen anywhere

        def gain(node: TreeNode | None) -> int:
            nonlocal best
            if node is None:
                return 0                      # empty extension contributes 0
            # Clamped at 0: never extend the path into a losing subtree.
            left = max(gain(node.left), 0)
            right = max(gain(node.right), 0)
            # Best path whose highest point is this node.
            best = max(best, node.val + left + right)
            # Downward path through this node uses at most one child leg.
            return node.val + max(left, right)

        gain(root)
        return best
