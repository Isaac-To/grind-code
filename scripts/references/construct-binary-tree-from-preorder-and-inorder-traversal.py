"""Reference solution — 105. Construct Binary Tree from Preorder and Inorder Traversal.

Approach: recursion with a value->index map over `inorder`. The first
unconsumed preorder value is always the subtree root; its position in
`inorder` splits the remaining values into the left and right subtrees.
Pre-consuming the preorder list from the front (via an index pointer, not
pops) keeps everything O(1) per node.

Invariant: build(left_count_fixed...) — more precisely, every call to
_build() consumes exactly one preorder entry (the next root) and claims a
contiguous slice of inorder identified by [in_lo, in_hi). The root index in
inorder partitions that slice: positions before it are the left subtree's
values (the same count of following preorder entries), positions after it
the right subtree's. Because values are unique, the map lookup is exact.

Complexity: O(n) time — each node created once, each inorder index visited
once; O(n) space for the map plus O(h) recursion stack.
"""
from __future__ import annotations


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def buildTree(self, preorder: list[int], inorder: list[int]) -> TreeNode | None:
        # Root value -> its index in inorder, for O(1) slicing decisions.
        index_of = {value: i for i, value in enumerate(inorder)}
        self._next = 0  # position of the next unconsumed preorder entry

        def build(in_lo: int, in_hi: int) -> TreeNode | None:
            # inorder slice [in_lo, in_hi) is empty: this subtree is null.
            if in_lo >= in_hi:
                return None
            root_val = preorder[self._next]
            self._next += 1              # preorder front is consumed as the root
            mid = index_of[root_val]     # splits this slice into left/right
            left = build(in_lo, mid)     # consumes exactly its preorder entries
            right = build(mid + 1, in_hi)
            return TreeNode(root_val, left, right)

        return build(0, len(inorder))
