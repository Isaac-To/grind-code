"""Reference solution — 127. Word Ladder.

Approach: BFS over an implicit graph whose nodes are words and whose
edges join words differing by exactly one letter. To enumerate a word's
neighbours cheaply, bucket every word by its "wildcard patterns"
("*ot", "h*t", "ho*"): two words sharing a pattern are neighbours.
BFS from beginWord gives the shortest sequence length; the answer
counts *words*, so the number of levels is the length.

Invariant: `visited` only contains fully-processed words, so the BFS
expands strictly level by level; the first time endWord appears it is
at its minimal distance. If the queue empties first, no sequence exists
and we return 0.

Complexity: O(N * L^2) time to build buckets (N words of length L) plus
BFS work; O(N * L) space for buckets and visited.
"""
from __future__ import annotations

from collections import deque


class Solution:
    def ladderLength(self, beginWord: str, endWord: str, wordList: list[str]) -> int:
        words = set(wordList)              # O(1) membership / removal
        if endWord not in words:
            return 0                       # target unreachable by definition

        # bucket[wildcard] = all words matching that one-letter-blank pattern
        buckets: dict[str, list[str]] = {}
        for word in words:
            for i in range(len(word)):
                buckets.setdefault(word[:i] + "*" + word[i + 1:], []).append(word)

        queue = deque([beginWord])
        length = 1                          # counts beginWord itself
        while queue:
            for _ in range(len(queue)):      # process one BFS level = one hop
                word = queue.popleft()
                if word == endWord:
                    return length           # first hit is shortest (BFS levels)
                for i in range(len(word)):
                    pattern = word[:i] + "*" + word[i + 1:]
                    for nxt in buckets.get(pattern, ()):
                        if nxt in words:     # not yet used as a rung
                            words.discard(nxt)   # mark visited by removing
                            queue.append(nxt)
            length += 1                     # every extra level is one more word
        return 0                            # endWord never reached
