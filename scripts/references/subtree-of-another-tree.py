"""Reference solution — 572. Subtree of Another Tree.

Approach: for every node of `root`, test whether the subtree rooted there is
*identical* to `subRoot` (the same-tree check), reusing the classic
isSameTree recursion. Any match anywhere means subRoot is a subtree.

Invariant: subRoot is a subtree of root iff some node `n` of root satisfies
same(n, subRoot), because "subtree" means the node plus *all* of its
descendants — so subtree identity is exactly whole-tree identity at that
root. Pruning: we only descend when the candidate node's value already
matches subRoot's value.

Complexity: O(m * n) time in the worst case (m nodes in root, each compared
against a size-n pattern); O(h) space for the recursion stack.
"""
from __future__ import annotations


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def isSubtree(self, root: TreeNode | None, subRoot: TreeNode | None) -> bool:
        # An empty pattern matches trivially; a nonempty pattern needs nodes.
        if subRoot is None:
            return True
        if root is None:
            return False
        # Either the subtree starting at root IS the pattern,
        # or the pattern lives strictly in one of the child subtrees.
        return (
            self._same(root, subRoot)
            or self.isSubtree(root.left, subRoot)
            or self.isSubtree(root.right, subRoot)
        )

    def _same(self, a: TreeNode | None, b: TreeNode | None) -> bool:
        """Whole-tree equality: structure and values must match exactly."""
        if a is None and b is None:
            return True
        if a is None or b is None:
            return False
        return (
            a.val == b.val
            and self._same(a.left, b.left)
            and self._same(a.right, b.right)
        )
