"""Reference solution — 102. Binary Tree Level Order Traversal.

Approach: classic BFS with a queue holding exactly one level's worth of
nodes at a time. Snapshot the queue's length, drain that many nodes into the
current level's list, and push their children — which become the next level.

Invariant: at the top of each iteration, `queue` contains precisely the
nodes of one complete level in left-to-right order (children are pushed in
left-then-right order and FIFO preserves that). The level_count snapshot
separates the current level from the children appended while draining it.

Complexity: O(n) time — every node is enqueued and dequeued once;
O(w) extra space, where w is the maximum level width (up to n/2).
"""
from __future__ import annotations

from collections import deque


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def levelOrder(self, root: TreeNode | None) -> list[list[int]]:
        if root is None:              # empty tree has no levels at all
            return []
        result: list[list[int]] = []
        queue = deque([root])         # holds exactly one level, left to right
        while queue:
            level_count = len(queue)   # nodes belonging to the current level
            level: list[int] = []
            for _ in range(level_count):
                node = queue.popleft()
                level.append(node.val)
                # Queue up the next level's members in left-to-right order.
                if node.left is not None:
                    queue.append(node.left)
                if node.right is not None:
                    queue.append(node.right)
            result.append(level)
        return result
