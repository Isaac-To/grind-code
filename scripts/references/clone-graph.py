"""Reference solution — 133. Clone Graph.

Approach: one DFS pass that builds the copy lazily. For each original node
we look up (or create) its clone in a dictionary, then recurse over the
neighbour list. The dictionary is both the memo and the visited set, so
the cyclic links of the graph are rewired to already-created clones
instead of recursing forever.

Invariant: `old_to_new` maps exactly the nodes already fully wired into
the clone graph; entering a DFS call for a node already in the map returns
its finished clone immediately, which is what terminates the recursion on
cycles.

Complexity: O(V + E) time — each node and edge processed once; O(V) space
for the map and the recursion stack.
"""
from __future__ import annotations
from typing import Optional


class Node:
    """Graph node used by the runner (sem: graph)."""
    def __init__(self, val: int = 0, neighbors: Optional[list["Node"]] = None):
        self.val = val
        self.neighbors = neighbors if neighbors is not None else []


class Solution:
    def cloneGraph(self, node: Optional['Node']) -> Optional['Node']:
        # The runner hands an unconverted [] for the empty graph, so guard
        # on the Node type itself rather than on None alone.
        if not isinstance(node, Node):
            return None                      # empty graph -> empty graph

        old_to_new: dict[Node, Node] = {}   # original node -> its clone

        def dfs(cur: Node) -> Node:
            if cur in old_to_new:           # clone already built: breaks the cycle
                return old_to_new[cur]
            copy = Node(cur.val)            # create first, so neighbours can link to it
            old_to_new[cur] = copy          # register BEFORE recursing (cycle safety)
            copy.neighbors = [dfs(n) for n in cur.neighbors]
            return copy

        return dfs(node)
