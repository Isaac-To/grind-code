"""Reference solution — 199. Binary Tree Right Side View.

Approach: level-by-level BFS; the last node drained from each level is the
rightmost node of that level, which is exactly what an observer on the
right sees. Collect that one value per level.

Invariant: processing levels in FIFO order guarantees the final node popped
for a level is its rightmost member — children are pushed left-then-right,
so the queue orders each level with the rightmost node last. Note "right
side view" does NOT mean "follow right pointers only": a deep left subtree
can be visible when the right side is shallower (the queue handles this
automatically because it tracks full levels).

Complexity: O(n) time — each node enters the queue once; O(w) space for the
queue, where w is the widest level.
"""
from __future__ import annotations

from collections import deque


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def rightSideView(self, root: TreeNode | None) -> list[int]:
        if root is None:               # nothing to look at
            return []
        view: list[int] = []
        queue = deque([root])           # exactly one level at a time
        while queue:
            level_count = len(queue)    # size of the current level
            for i in range(level_count):
                node = queue.popleft()
                if i == level_count - 1:  # last of the level = rightmost
                    view.append(node.val)
                if node.left is not None:
                    queue.append(node.left)
                if node.right is not None:
                    queue.append(node.right)
        return view
