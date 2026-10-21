"""Reference solution — 230. Kth Smallest Element in a BST.

Approach: iterative in-order traversal with early exit. In-order visits BST
values ascending, so the kth node visited is the kth smallest. Stop as soon
as k nodes have been popped.

Invariant: values are popped from the stack in strictly increasing order
(the classic left-self-right pattern), so the counter ticks once per value
in sorted order; when it reaches k, the current node's value is the answer.
The iterative form lets us stop mid-traversal, which plain recursion makes
awkward.

Complexity: O(h + k) time — descend h nodes, then visit k; O(h) space for
the stack.
"""
from __future__ import annotations


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def kthSmallest(self, root: TreeNode | None, k: int) -> int:
        stack: list[TreeNode] = []
        node = root
        count = 0                     # how many values visited in sorted order
        while stack or node is not None:
            # Slide to the leftmost unvisited node, stacking the path.
            while node is not None:
                stack.append(node)
                node = node.left
            node = stack.pop()        # next smallest value in the whole tree
            count += 1
            if count == k:            # kth smallest reached: stop early
                return node.val
            node = node.right         # the right subtree holds larger values
        raise ValueError("k exceeds the number of nodes")  # unreachable per constraints
