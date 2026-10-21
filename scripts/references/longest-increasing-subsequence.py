"""Reference solution — 300. Longest Increasing Subsequence.

Approach: patience-sorting / tails DP. `tails[k]` is the smallest possible
tail value of any increasing subsequence of length k+1 seen so far. tails
is kept sorted (proved below), so for each new number x we binary-search
for the first tails element >= x and replace it with x — or append x if
x is larger than everything, extending the longest subsequence.

Why tails stays sorted and correct: replacing tails[k] with a smaller-or-
equal tail of the same length keeps the invariant "tails[k] is the minimum
tail among length-(k+1) subsequences" — x extends some subsequence of length
k (its tail tails[k-1] < x... more precisely, the element replaced had the
same length budget and x >= the old tail's predecessor chain works because
tails is sorted). The answer is len(tails), the longest length ever achieved.

Invariant (the crux): tails is strictly increasing at all times. When x
replaces tails[k] via the first index with tails[k] >= x, all elements
before position k are < x, so x can serve as the tail of a length-(k+1)
subsequence; and x <= old tails[k], so the minimum only improves.

Strictness: "increasing" means strictly increasing, hence we replace on
ties (bisect_left) rather than extend — duplicates do NOT lengthen the LIS.

Complexity: O(n log n) time (one binary search per element), O(n) space.
"""
from __future__ import annotations

from bisect import bisect_left


class Solution:
    def lengthOfLIS(self, nums: list[int]) -> int:
        tails: list[int] = []              # tails[k] = min tail of a length-(k+1) IS
        for x in nums:
            # first position whose tail is >= x; equal tails are replaced
            k = bisect_left(tails, x)
            if k == len(tails):
                tails.append(x)            # x extends the longest subsequence
            else:
                tails[k] = x               # cheaper tail for length k+1
        return len(tails)
