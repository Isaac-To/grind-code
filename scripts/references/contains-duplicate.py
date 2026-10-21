"""Reference solution — 217. Contains Duplicate.

Approach: put every element into a hash set as we scan; if an element is
already present, a duplicate exists. A set gives O(1) average membership
tests, so one pass settles the question.

Invariant: at the moment we process nums[i], the set contains exactly the
distinct values of nums[0..i-1]. So `nums[i] in seen` is true iff nums[i]
duplicates some earlier element — the earliest such i is when we report
True. If the scan finishes, no element ever repeated.

Complexity: O(n) time (n insertions/probes), O(n) space for the set.
An O(1)-space alternative is sort-then-scan at O(n log n) time.
"""
from __future__ import annotations


class Solution:
    def containsDuplicate(self, nums: list[int]) -> bool:
        seen: set[int] = set()      # distinct values encountered so far
        for value in nums:
            if value in seen:       # this value appeared earlier -> duplicate
                return True
            seen.add(value)         # remember it for future comparisons
        return False                # scan finished: every value was distinct
