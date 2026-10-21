"""Reference solution — 1448. Count Good Nodes in Binary Tree.

Approach: DFS carrying the maximum value seen on the root-to-current path.
A node is "good" iff its value is >= that running path maximum. Passing
`max(value, path_max)` down each branch keeps the state local — no need to
store the whole path.

Invariant: when dfs(node, path_max) is called, path_max equals the largest
node value on the path from the root to node's parent (root included), so
the single comparison node.val >= path_max decides goodness correctly for
the exact path LeetCode defines. Strict `>=` (not `>`) means ties count as
good.

Note: the root has no ancestors, so its own value is its path maximum —
that's why the initial call seeds with root.val. (Using -infinity as the
seed also works and makes the root trivially good.)

Complexity: O(n) time — every node visited once; O(h) space for the
recursion stack.
"""
from __future__ import annotations


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def goodNodes(self, root: TreeNode) -> int:
        def dfs(node: TreeNode | None, path_max: int) -> int:
            if node is None:
                return 0                     # empty subtree contributes nothing
            # This node is good iff it matches or beats the path maximum.
            good = 1 if node.val >= path_max else 0
            # Descend with the tightest maximum accumulated so far.
            next_max = max(path_max, node.val)
            return good + dfs(node.left, next_max) + dfs(node.right, next_max)

        return dfs(root, root.val)           # root's path maximum is itself
