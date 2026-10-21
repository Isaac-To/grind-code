"""Reference solution — 49. Group Anagrams.

Approach: two strings are anagrams iff sorting their characters yields the
same sequence. Use that sorted tuple as a canonical key in a dict from
key -> list of strings; every anagram class lands in the same bucket.

Invariant: for any two strings in the same bucket, their sorted tuples
are equal, hence they are anagrams; strings with different sorted tuples
land in different buckets, so groups are exactly the anagram classes.

Complexity: O(n * k log k) time for n strings of length <= k (sorting
dominates); O(n * k) space for the output. A counting-sort key
(26-tuple of letter counts) gives O(n * k) time if desired.
"""
from __future__ import annotations


class Solution:
    def groupAnagrams(self, strs: list[str]) -> list[list[str]]:
        groups: dict[tuple[str, ...], list[str]] = {}
        for s in strs:
            key = tuple(sorted(s))   # canonical form shared by all anagrams
            groups.setdefault(key, []).append(s)   # bucket strings by class
        # Dict preserves insertion order, so output order is deterministic
        # (first-appearance order of each class) — fine since any order passes.
        return list(groups.values())
