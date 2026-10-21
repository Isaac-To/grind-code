"""Reference solution — 295. Find Median from Data Stream.

Approach: two heaps splitting the stream in half.
  - `low`  : a max-heap (stored negated) holding the smaller half;
  - `high` : a min-heap holding the larger half.
Every addNum rebalances so that len(low) is len(high) or len(high) + 1.
The median then reads off the roots: the max of the lower half when the
count is odd, else the average of the two roots.

Invariant: every element of low <= every element of high, and the size rule
above pins the middle position(s). addNum maintains it by pushing the new
number into low, then moving low's max into high (guaranteeing the ordering
across the halves), then moving high's min back if low got too small.

Complexity: O(log n) per addNum, O(1) findMedian; O(n) space.
"""
import heapq


class MedianFinder:

    def __init__(self):
        self.low = []    # smaller half as negated values -> max-heap
        self.high = []   # larger half -> plain min-heap

    def addNum(self, num: int) -> None:
        heapq.heappush(self.low, -num)            # trial: num belongs to the lower half
        heapq.heappush(self.high, -heapq.heappop(self.low))  # move low's max across:
        # this is the only element that might violate low <= high
        if len(self.high) > len(self.low):        # rebalance: low may hold one extra,
            heapq.heappush(self.low, -heapq.heappop(self.high))  # never two

    def findMedian(self) -> float:
        if len(self.low) > len(self.high):        # odd count: middle is low's max
            return float(-self.low[0])
        return (-self.low[0] + self.high[0]) / 2  # even: average of the two roots
