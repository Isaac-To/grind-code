"""Reference solution — 211. Design Add and Search Words Data Structure.

Approach: same trie as 208 for addWord. search must additionally handle the
wildcard '.', which matches any single letter, so a query is answered by a
recursive DFS over the trie: at a normal letter, follow exactly one child;
at '.', fan out over all 26 children and succeed if any branch matches.
The empty string (end of pattern) succeeds iff the current node's is_end
flag is set.

Invariant: _match(node, i) returns True iff the trie rooted at `node`
contains some inserted word whose suffix word[i:] equals pattern[i:],
treating each '.' in the pattern as a wildcard for one letter. The public
search just seeds this recursion at the root with i = 0. Because a trie
shares prefixes, a failed branch dies as soon as the path breaks — we
never re-scan the whole dictionary per query.

Complexity: addWord is O(L). search is O(26^D · L) in the worst case, where
D is the number of dots (each dot can branch 26 ways); the problem
guarantees D <= 2, so queries stay near-linear in practice. Space is
O(total characters added).
"""
from __future__ import annotations


class TrieNode:
    __slots__ = ("children", "is_end")

    def __init__(self) -> None:
        self.children: dict[str, TrieNode] = {}  # letter -> next node
        self.is_end = False  # True iff an added word terminates here


class WordDictionary:

    def __init__(self):
        self.root = TrieNode()  # represents the empty prefix

    def addWord(self, word: str) -> None:
        node = self.root
        for ch in word:                    # walk/create one node per character
            if ch not in node.children:     # first time this prefix appears
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.is_end = True                 # mark the word's final node

    def search(self, word: str) -> bool:
        return self._match(self.root, word, 0)

    def _match(self, node: TrieNode, word: str, i: int) -> bool:
        """True iff some added word's suffix from position i equals
        word[i:] under the wildcard semantics of '.'."""
        if i == len(word):                 # pattern exhausted: need a word end here
            return node.is_end
        ch = word[i]
        if ch == ".":                      # wildcard: try every branch, OR them
            return any(self._match(child, word, i + 1)
                       for child in node.children.values())
        child = node.children.get(ch)      # normal letter: single forced branch
        return child is not None and self._match(child, word, i + 1)
