"""Reference solution — 269. Alien Dictionary.

Approach: topological sort (Kahn's algorithm) on a graph whose letters are
nodes and whose edges are precedence rules extracted from adjacent word
pairs. For each consecutive pair (w1, w2), scan for the first differing
position: that gives an edge w1[pos] -> w2[pos]. If w2 is a proper prefix of
w1 (e.g. "abc" before "ab"), the ordering is contradictory — return "".

Invariant: every edge u -> v asserts "u precedes v" in the alien alphabet,
because the dictionary is sorted, so any valid ordering must be a
topological order of this graph. Kahn's algorithm peels off zero-in-degree
letters one at a time; if the process consumes every letter, that order is
consistent. If it stalls first, a cycle exists (contradictory rules) and we
return "". Letters never compared by any rule may appear anywhere — we seed
the queue with all letters, ordered alphabetically for determinism.

Complexity: O(total letters + rules) time — each character is scanned once
per adjacent pair and each edge is processed once; O(1) space (≤ 26 letters).
"""
from __future__ import annotations

from collections import deque
from typing import List


class Solution:
    def alienOrder(self, words: List[str]) -> str:
        # collect the full letter set first — letters that appear in no rule
        # still belong in the output alphabet
        letters = set("".join(words))
        adj = {ch: set() for ch in letters}  # ch -> letters that must follow it
        indeg = {ch: 0 for ch in letters}

        for w1, w2 in zip(words, words[1:]):
            # find the first position where the sorted pair differs
            for a, b in zip(w1, w2):
                if a != b:
                    if b not in adj[a]:  # dedupe: identical rules count once
                        adj[a].add(b)
                        indeg[b] += 1
                    break  # letters after the first difference carry no info
            else:
                # no differing char found: w2 must not be a strict prefix of w1
                if len(w2) < len(w1):
                    return ""  # e.g. ["abc","ab"] is impossible to satisfy

        # Kahn's algorithm; sorted start keeps the output deterministic
        queue = deque(sorted(ch for ch in letters if indeg[ch] == 0))
        order = []
        while queue:
            ch = queue.popleft()
            order.append(ch)
            for nxt in adj[ch]:
                indeg[nxt] -= 1
                if indeg[nxt] == 0:
                    queue.append(nxt)

        return "".join(order) if len(order) == len(letters) else ""  # cycle
