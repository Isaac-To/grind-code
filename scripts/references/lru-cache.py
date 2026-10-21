"""Reference solution — 146. LRU Cache.

Approach: hash map + doubly linked list. The map gives O(1) key lookup;
the list encodes recency order, most recently used at the head (right
after `dummy`). Each map value stores its list node, so both `get` and
`put` can unlink a node and re-insert it at the front in O(1) without
scanning.

Invariant: the doubly linked list, read from `dummy` forward, is exactly
the cache's keys ordered most-recent → least-recent. Therefore eviction
is always the node just before `tail_sentinel`, and any touch moves a
node to just after `head_sentinel`.

Why doubly linked: a node can be unlinked with only a pointer to itself
(prev.next / next.prev), which is what makes O(1) removal from the middle
possible — a singly linked list would need the predecessor.

Python's OrderedDict would do this in fewer lines; the explicit version
below shows the machinery the problem is designed to teach.

Complexity: O(1) time per get/put; O(capacity) space.
"""
from __future__ import annotations


class Node:
    """A (key, value) entry, doubling as a node of the recency list."""
    def __init__(self, key=0, value=0):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None


class LRUCache:
    def __init__(self, capacity: int):
        self.cap = capacity
        self.map = {}                      # key -> Node
        # Sentinels: head <-> ... <-> tail; real nodes live between them.
        self.head, self.tail = Node(), Node()
        self.head.next, self.tail.prev = self.tail, self.head

    def _remove(self, node: Node) -> None:
        """Unlink a node from anywhere in the list, O(1)."""
        node.prev.next = node.next
        node.next.prev = node.prev

    def _add_front(self, node: Node) -> None:
        """Insert a node as the most recently used, O(1)."""
        node.next = self.head.next         # wire node -> old front
        node.prev = self.head              # wire head -> node
        self.head.next.prev = node
        self.head.next = node

    def get(self, key: int) -> int:
        if key not in self.map:
            return -1
        node = self.map[key]
        self._remove(node)                 # a read counts as a use
        self._add_front(node)
        return node.value

    def put(self, key: int, value: int) -> None:
        if key in self.map:                # existing key: drop its old node
            self._remove(self.map[key])
        node = Node(key, value)
        self.map[key] = node
        self._add_front(node)
        if len(self.map) > self.cap:       # over capacity: evict the LRU node
            lru = self.tail.prev           # least recent = node before tail
            self._remove(lru)
            del self.map[lru.key]          # keep map and list in sync
