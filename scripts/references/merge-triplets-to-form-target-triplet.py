"""Reference solution — 1899. Merge Triplets to Form Target Triplet.

Approach: a triplet with any coordinate *larger* than the target's
corresponding coordinate is poison — max-merging only grows coordinates, so
it can never be removed. Discard all such triplets.

Among the survivors (every coordinate <= target), merging can only move each
coordinate toward the target. The target is reachable iff, for each
coordinate position k, some surviving triplet has triplet[k] == target[k] —
then merging those three (or fewer) survivors coordinate-wise yields exactly
the target: every coordinate is <= target and at least one equals it.

Complexity: O(n) time, O(1) space.
"""
from __future__ import annotations


class Solution:
    def mergeTriplets(self, triplets: list[list[int]], target: list[int]) -> bool:
        # Marks whether each coordinate of the target is achievable
        # using only triplets that never overshoot the target.
        found = [False, False, False]
        for t in triplets:
            if all(t[k] <= target[k] for k in range(3)):   # safe to merge
                for k in range(3):
                    if t[k] == target[k]:
                        found[k] = True
        return all(found)
