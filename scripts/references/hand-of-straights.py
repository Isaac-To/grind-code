"""Reference solution — 846. Hand of Straights.

Approach: greedy on the smallest remaining card. Sort the hand; for each
group we must consume the smallest card still in hand (nothing else can pair
with a value below it). From that card v, greedily take one card of each of
v, v+1, ..., v+groupSize-1. If any of those values is missing, the smallest
card can never be grouped — return False.

Invariant: we only ever remove cards that any valid grouping must also use
together, so failure here means failure globally; success consumes all cards.

Implementation: count occurrences with a dict, walk sorted unique values,
and subtract one from each of the groupSize consecutive counts starting at
the smallest value with a nonzero count.

Complexity: O(n log n) time (sort dominates), O(n) space for the counts.
"""
from __future__ import annotations

from collections import Counter


class Solution:
    def isNStraightHand(self, hand: list[int], groupSize: int) -> bool:
        if len(hand) % groupSize != 0:
            return False                # cannot split into equal-size groups
        counts = Counter(hand)
        for value in sorted(counts):    # smallest available value first
            need = counts[value]
            if need == 0:
                continue                # already fully consumed by earlier groups
            # Every group starting here needs `need` copies of each next value.
            for v in range(value, value + groupSize):
                if counts[v] < need:
                    return False       # missing card: `value` can never be grouped
                counts[v] -= need       # reserve one copy per group for this value
        return True
