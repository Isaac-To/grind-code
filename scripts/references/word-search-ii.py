"""Reference solution — 212. Word Search II.

Approach: build a trie of the words, then run one DFS from every board
cell, walking *down the trie as we step on letters*. A step is legal only
if the current trie node has a child for that letter, so the trie prunes
every path that starts no word — that is the key speed-up over running
word-search per word.

When a DFS path lands on a node flagged is_end, the spelled string is a
word: record it and unflag the node so duplicates are never reported
twice. Nodes left with no words in their subtree are pruned after the DFS
backtracks past them (deleting the child pointer), which bounds the walk
and gives near-linear behavior in practice.

Invariant: DFS(cell, node) explores exactly the board paths whose spelled
strings are prefixes of words stored in node's subtree; a word is emitted
iff its full path exists in the trie, is spellable on the board with no
repeated cell, and ends on an un-emitted is_end node. Cells are marked
'#' while inside the current path so a path never revisits a cell, and
restored on backtrack so other paths may use it.

Complexity: worst case O(m·n·4·3^(L-1)) where L is the max word length
(the first step has 4 neighbours, later steps at most 3 since we came
from somewhere); trie pruning makes typical behavior far better. Space:
O(total word characters) for the trie plus O(L) recursion stack.
"""
from __future__ import annotations


class TrieNode:
    __slots__ = ("children", "is_end")

    def __init__(self) -> None:
        self.children: dict[str, TrieNode] = {}  # letter -> next node
        self.is_end = False                      # a word terminates here


class Solution:
    def findWords(self, board: list[list[str]], words: list[str]) -> list[str]:
        # -- build the trie of query words --
        root = TrieNode()
        for word in words:
            node = root
            for ch in word:
                if ch not in node.children:
                    node.children[ch] = TrieNode()
                node = node.children[ch]
            node.is_end = True

        rows, cols = len(board), len(board[0])
        found: list[str] = []

        def dfs(r: int, c: int, node: TrieNode, path: list[str]) -> None:
            """Explore cell (r, c) having already matched `path` of letters."""
            ch = board[r][c]
            nxt = node.children.get(ch)
            if nxt is None:              # no word in the trie spells this step
                return

            path.append(ch)
            board[r][c] = "#"           # mark visited for THIS path only
            if nxt.is_end:              # path spells a complete word
                found.append("".join(path))
                nxt.is_end = False      # never report the same word twice

            # step to the four orthogonal neighbours that stay on the board
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if 0 <= nr < rows and 0 <= nc < cols and board[nr][nc] != "#":
                    dfs(nr, nc, nxt, path)

            board[r][c] = ch            # un-visit so other paths can use it
            path.pop()

            # prune: if nothing below `nxt` can ever match again, drop it
            if not nxt.children and not nxt.is_end:
                del node.children[ch]

        for r in range(rows):           # every cell is a potential word start
            for c in range(cols):
                dfs(r, c, root, [])
        return found
