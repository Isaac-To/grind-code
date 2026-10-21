"""Reference solution — 347. Top K Frequent Elements.

Approach: bucket sort by frequency. First count occurrences of each value;
then place each value into bucket[count] where count is its frequency.
Scanning buckets from the highest possible frequency (n) downward and
collecting values gives the k most frequent in O(n) total — better than
the O(n log n) bound demanded by the follow-up.

Invariant: after bucketing, bucket[c] holds exactly the values occurring
c times. Emitting values from high buckets to low therefore yields
values in non-increasing frequency order; taking the first k gives the
answer (the problem guarantees it is unique, so no tie-breaking is
ambiguous).

Complexity: O(n) time, O(n) space.
"""
from __future__ import annotations


class Solution:
    def topKFrequent(self, nums: list[int], k: int) -> list[int]:
        counts: dict[int, int] = {}
        for value in nums:                 # frequency of each value
            counts[value] = counts.get(value, 0) + 1

        n = len(nums)
        buckets: list[list[int]] = [[] for _ in range(n + 1)]  # freq 1..n
        for value, count in counts.items():
            buckets[count].append(value)   # value lands in its frequency bucket

        answer: list[int] = []
        for freq in range(n, 0, -1):       # highest frequency first
            for value in buckets[freq]:
                answer.append(value)
                if len(answer) == k:       # collected enough — stop early
                    return answer
        return answer                      # unreachable when k <= #unique values
