"""Reference solution — 235. Lowest Common Ancestor of a Binary Search Tree.

Approach: exploit BST order, no parent pointers or path recording needed.
Start at the root and walk down: if both p and q are smaller than the
current node, their LCA is in the left subtree; if both are larger, it is in
the right subtree. The first node where they *split* (or where one equals
the current value) is the LCA.

Invariant: at every step, `node` is an ancestor of both p and q (they lie
inside its subtree), so the loop can never fall off the tree. The answer is
the first ancestor at or below the root whose value sits between p and q
inclusive — that node is a common ancestor, and any deeper ancestor of both
would have to lie strictly on one side, contradicting the split. Since all
values are unique, comparisons are unambiguous.

Complexity: O(h) time — one root-to-LCA walk; O(1) space — iterative loop.
"""
from __future__ import annotations


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def lowestCommonAncestor(self, root: 'TreeNode', p: 'TreeNode', q: 'TreeNode') -> 'TreeNode':
        node = root
        while node is not None:
            if p.val < node.val and q.val < node.val:
                node = node.left     # both targets live left: LCA is deeper
            elif p.val > node.val and q.val > node.val:
                node = node.right    # both targets live right: keep walking
            else:
                return node          # targets split (or one is the node): LCA
        return node                  # unreachable when p, q exist in the tree
