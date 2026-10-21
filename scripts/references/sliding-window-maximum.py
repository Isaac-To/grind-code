"""Reference solution — 239. Sliding Window Maximum.

Approach: monotonic decreasing deque of indices. The deque holds indices of
"candidate maxima": their values are strictly decreasing from front to back.
The front is always the index of the maximum of the current window.

Invariants (after processing index i):
  - every index in the deque lies within the window [i - k + 1, i],
  - their values are in strictly decreasing order.

Why it stays true:
  - Before pushing i we pop from the back every index whose value is
    <= nums[i]: those can never be a window maximum again — any future
    window containing them also contains the newer, >= value nums[i].
    (Popping equal values keeps the deque strict and is still safe.)
  - If the front index has slid out of the window (< i - k + 1) we pop it;
    since the front is the oldest index and the window edge moves by one,
    at most one eviction per step suffices.

Hence, once the first full window forms (i >= k - 1), nums[deque[0]] is
exactly the max of that window.

Complexity: O(n) time — each index is pushed and popped at most once;
O(k) space — the deque never holds more than k indices.
"""
from __future__ import annotations

from collections import deque


class Solution:
    def maxSlidingWindow(self, nums: list[int], k: int) -> list[int]:
        dq: deque[int] = deque()  # indices, values strictly decreasing front->back
        result: list[int] = []
        for i, value in enumerate(nums):
            # Drop candidates that the new value dominates.
            while dq and nums[dq[-1]] <= value:
                dq.pop()
            dq.append(i)
            if dq[0] <= i - k:    # front has left the window on the left
                dq.popleft()
            if i >= k - 1:        # first full window is complete
                result.append(nums[dq[0]])
        return result
