"""Reference solution — 84. Largest Rectangle in Histogram.

Approach: monotonic increasing stack of indices. For each bar we want
the widest rectangle whose height is exactly that bar's height: extend
left to the previous shorter bar and right to the next shorter bar.
The stack gives both boundaries cheaply.

Invariant: heights at stack indices are strictly increasing bottom-to-top.
When the current bar is shorter than the top of the stack, the top bar
has just found its *right* boundary (the current index) and its *left*
boundary is the new stack top after popping. Its rectangle's height is
its own height; its width is (right - left - 1).

The sentinel bar of height 0 appended at the end flushes every bar off
the stack so no second loop is needed; an explicit 0 pushed at the start
lets the leftmost real bar have a proper "previous" element.

Complexity: O(n) time — each index is pushed and popped at most once;
O(n) space for the stack.
"""
from __future__ import annotations


class Solution:
    def largestRectangleArea(self, heights: list[int]) -> int:
        best = 0
        stack = []  # indices of bars with strictly increasing heights
        for i, h in enumerate(heights + [0]):  # sentinel 0 forces a final full flush
            while stack and heights[stack[-1]] > h:
                height = heights[stack.pop()]  # bar whose rectangle we now finalize
                left = stack[-1] if stack else -1  # nearest shorter bar to the left
                width = i - left - 1  # bars strictly between the two boundaries
                best = max(best, height * width)
            stack.append(i)
        return best
