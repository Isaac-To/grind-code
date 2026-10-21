"""Reference solution — 703. Kth Largest Element in a Stream.

Approach: keep a *min-heap* of at most k elements — the k largest seen so far.
The heap's root is then exactly the k-th largest value, which is what `add`
must report. On each `add(val)`:
  1. push val (heap size may become k + 1),
  2. if the heap now holds more than k elements, pop the smallest — the
     survivors are the k largest values seen so far,
  3. return the root, the smallest of those k largest = the k-th largest.

Invariant: after every operation the heap contains exactly the k largest
values of the stream (or all of them if fewer than k arrived), so its minimum
is the k-th largest. A min-heap (not a max-heap) is the right tool because
we repeatedly evict the *smallest* of the top-k, which is an O(log k) root pop.

Complexity: O(len(nums) · log k) to build, O(log k) per add; O(k) space.
"""
import heapq


class KthLargest:

    def __init__(self, k: int, nums: list[int]):
        self.k = k
        self.heap = list(nums)          # copy so we never mutate the caller's list
        heapq.heapify(self.heap)       # min-heap: root is the smallest element
        while len(self.heap) > self.k:  # shed everything outside the top-k
            heapq.heappop(self.heap)

    def add(self, val: int) -> int:
        heapq.heappush(self.heap, val)  # candidate for the top-k
        if len(self.heap) > self.k:     # too many: drop the smallest
            heapq.heappop(self.heap)
        return self.heap[0]            # smallest of the k largest = k-th largest
