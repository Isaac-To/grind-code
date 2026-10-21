"""Reference solution — 208. Implement Trie (Prefix Tree).

Approach: a trie is a tree of characters. Each node holds a fixed 26-slot
child table (one per lowercase letter) and a boolean flag marking "a word
ends here". insert walks down from the root, creating missing children as
it goes, then flags the last node. search and startsWith walk the same
path read-only; the only difference is that search additionally requires
the *end-of-word* flag on the final node, while startsWith only requires
the path to exist.

Invariant: after every operation, node.child[c] is the unique trie node
reachable by the string-prefix that ends in c, and node.is_end is True iff
some inserted word ends exactly at that node. Hence "did I ever insert s?"
is exactly "the path for s exists and its last node has is_end set", and
"is p a prefix of some inserted word?" is exactly "the path for p exists".

Complexity: each operation walks one character per letter — O(L) time for
a word of length L (O(26·L) if you count child-table allocation for
insert); O(total characters inserted) space overall.
"""
from __future__ import annotations


class TrieNode:
    __slots__ = ("children", "is_end")

    def __init__(self) -> None:
        self.children: list[TrieNode | None] = [None] * 26  # one slot per 'a'..'z'
        self.is_end = False  # True iff an inserted word terminates at this node


class Trie:

    def __init__(self):
        self.root = TrieNode()  # the empty prefix; every word hangs off it

    def insert(self, word: str) -> None:
        node = self.root
        for ch in word:                       # walk/create one node per character
            idx = ord(ch) - ord("a")          # map 'a'..'z' -> 0..25
            if node.children[idx] is None:   # first time this prefix appears
                node.children[idx] = TrieNode()
            node = node.children[idx]
        node.is_end = True                    # mark the word's final node

    def search(self, word: str) -> bool:
        node = self._walk(word)
        # the path must exist AND terminate at a flagged (word-end) node
        return node is not None and node.is_end

    def startsWith(self, prefix: str) -> bool:
        # any existing path of the right length proves some word has this prefix
        return self._walk(prefix) is not None

    def _walk(self, s: str) -> TrieNode | None:
        """Follow s from the root; return the final node, or None if the
        path breaks (some character has never been inserted at that depth)."""
        node = self.root
        for ch in s:
            node = node.children[ord(ch) - ord("a")]
            if node is None:  # dead end: no inserted word goes through s[:i+1]
                return None
        return node
