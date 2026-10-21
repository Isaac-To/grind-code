"""Reference solution — 4. Median of Two Sorted Arrays.

Approach: partition binary search on the SHORTER array only. A median split
cuts the combined m+n elements into a low half of size (m+n)//2. If nums1
contributes its first i elements to the low half, nums2 must contribute
j = (m+n+1)//2 - i (the +1 handles odd totals by biasing the low half to be
the bigger one). The split is correct exactly when every element of the low
half is <= every element of the high half, which reduces to two checks:
nums1[i-1] <= nums2[j] and nums2[j-1] <= nums1[i] (edges = +/-infinity pass
trivially). When nums1[i-1] > nums2[j], i is too big; otherwise i is too
small. Binary search on i converges to the unique correct partition.

Invariant: the window [lo, hi] of feasible i values always contains the
correct cut. Each iteration discards half of it.

With the correct partition, the median is
  - odd  total: max(nums1[i-1], nums2[j-1])            (biggest of the low half)
  - even total: average of that max and min(nums1[i], nums2[j])
               (biggest of low half and smallest of high half).

Complexity: O(log(min(m, n))) time — the search runs over the shorter array;
O(1) space.
"""
from __future__ import annotations


class Solution:
    def findMedianSortedArrays(self, nums1: list[int], nums2: list[int]) -> float:
        # Search the shorter array: fewer iterations AND guarantees j >= 0.
        if len(nums1) > len(nums2):
            nums1, nums2 = nums2, nums1
        m, n = len(nums1), len(nums2)
        lo, hi = 0, m                       # i = number of nums1 elements in the low half
        while lo <= hi:
            i = (lo + hi) // 2               # cut after i elements of nums1
            j = (m + n + 1) // 2 - i         # matching cut in nums2 keeps the halves sized
            # Values adjacent to the cut; infinity stands for "no neighbor on that side".
            left1 = nums1[i - 1] if i > 0 else float("-inf")
            right1 = nums1[i] if i < m else float("inf")
            left2 = nums2[j - 1] if j > 0 else float("-inf")
            right2 = nums2[j] if j < n else float("inf")
            if left1 <= right2 and left2 <= right1:   # correct partition found
                if (m + n) % 2:                          # odd total: median is the low half's max
                    return float(max(left1, left2))
                return (max(left1, left2) + min(right1, right2)) / 2  # average the middle two
            if left1 > right2:              # nums1's low part sticks too far right
                hi = i - 1                  # move the cut left in nums1
            else:                           # nums1's low part is too small
                lo = i + 1                  # move the cut right in nums1
        raise AssertionError("a valid partition always exists for sorted inputs")
