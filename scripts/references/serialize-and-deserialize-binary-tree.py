"""Reference solution — 297. Serialize and Deserialize Binary Tree.

Approach: preorder token stream. Serialize by writing each node's value, or
a marker ("#") for null, in preorder; deserialize by reading tokens in the
same order — the very next token always tells us what the next node is, so
no length or lookahead information is needed.

Invariant: both directions traverse the tree in the same preorder, and the
token stream encodes nulls explicitly, so the tree shape is fully
determined: at deserialize time, the iterator points at exactly the token
belonging to the next node to build. "#" consumes a null slot; a value
consumes a node plus, recursively, the token runs for its two children.

Why preorder (not level order): a node's entire subtree is contiguous in
the stream, which makes the recursive rebuild possible; the round trip
`deserialize(serialize(root))` restores the identical tree.

Complexity: O(n) time and O(n) space in both directions, n = node count.
"""
from __future__ import annotations


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

class Codec:

    def serialize(self, root: TreeNode | None) -> str:
        """Encodes a tree to a single comma-separated preorder string."""
        # The annotation matters: the runner converts a LeetCode array into
        # a real TreeNode only when the parameter is annotated as TreeNode.
        tokens: list[str] = []

        def walk(node: TreeNode | None) -> None:
            if node is None:
                tokens.append("#")           # explicit null marker
                return
            tokens.append(str(node.val))     # preorder: value before children
            walk(node.left)
            walk(node.right)

        walk(root)
        return ",".join(tokens)              # "" only when the tree is empty

    def deserialize(self, data: str) -> TreeNode | None:
        """Decodes the codec's string back to the original tree."""
        if not data:                         # empty string <=> empty tree
            return None
        tokens = data.split(",")
        pos = 0                              # index of the next unread token

        def build() -> TreeNode | None:
            nonlocal pos
            token = tokens[pos]
            pos += 1
            if token == "#":                # null marker: nothing to build
                return None
            node = TreeNode(int(token))
            node.left = build()             # children follow immediately
            node.right = build()
            return node

        return build()
