"""Reference solution — 875. Koko Eating Bananas.

Approach: binary search on the *answer* (the speed k), not on the piles.
The hours needed at speed k is sum(ceil(p / k) for p in piles), which is
non-increasing in k: if a speed works, every faster speed works too. That
monotonicity is exactly what binary search needs, so we hunt for the smallest
working k in the range [1, max(piles)] — speed max(piles) always finishes in
one hour per pile, so the answer can never exceed it.

Invariant (call mode): `hi + 1` is always a feasible speed and `lo - 1` is
never feasible at the point of the mid-test... concretely we keep the window
[lo, hi] such that the answer lies inside it; when hours_needed(mid) <= h the
answer is mid or smaller (record mid, search left), otherwise it is strictly
larger (search right).

Complexity: O(n log(max(piles))) time — each feasibility check is O(n) and
the window halves each of the log(max(piles)) iterations; O(1) extra space.
"""
from __future__ import annotations


class Solution:
    def minEatingSpeed(self, piles: list[int], h: int) -> int:
        def hours_needed(speed: int) -> int:
            # ceil(p/speed) without floats: (p + speed - 1) // speed
            return sum((pile + speed - 1) // speed for pile in piles)

        lo, hi = 1, max(piles)          # answer is a speed in [1, biggest pile]
        while lo < hi:                  # loop until lo == hi, the minimal feasible speed
            mid = (lo + hi) // 2        # candidate speed to test
            if hours_needed(mid) <= h:
                hi = mid                # mid works: the minimum is mid or smaller
            else:
                lo = mid + 1            # mid is too slow: the minimum is faster
        return lo                       # lo == hi: smallest speed finishing in time
