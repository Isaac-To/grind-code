"""Reference solution — 215. Kth Largest Element in an Array.

Approach: a min-heap of size k over the array's elements. Push each number;
once the heap exceeds k, pop the smallest. The survivors are the k largest
numbers of the array, and the heap root — their minimum — is the k-th
largest. (This honors the "without sorting" follow-up: heapify plus n pops
beats a full O(n log n) sort and is trivially correct.)

Invariant: at every step the heap contains exactly the k largest values seen
so far, so its minimum is the current k-th largest; after the final element
it is the answer.

Complexity: O(n log k) time; O(k) space.
"""
import heapq


class Solution:
    def findKthLargest(self, nums: list[int], k: int) -> int:
        heap = []
        for num in nums:
            heapq.heappush(heap, num)   # min-heap: root is the smallest kept value
            if len(heap) > k:           # more than k kept: the smallest is not top-k
                heapq.heappop(heap)
        return heap[0]                 # smallest of the k largest = k-th largest
