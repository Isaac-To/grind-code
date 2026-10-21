"""Reference solution — 739. Daily Temperatures.

Approach: monotonic decreasing stack of indices whose "next warmer day"
is still unknown. Walk left to right: while today's temperature beats
the temperature at the index on top of the stack, that day has found its
answer — the gap is today's index minus theirs — so pop it. Then push
today's index. Whatever stays on the stack never sees a warmer day and
keeps its default answer of 0.

Invariant: the stack's temperatures are strictly decreasing from bottom
to top, so each popped index is resolved exactly once, by its true next
warmer day (the first later index with a strictly larger temperature).

Note: equal temperatures do *not* pop — we need strictly warmer, so a
plateau stays on the stack.

Complexity: O(n) time — each index is pushed and popped at most once,
despite the nested while; O(n) space for the stack.
"""
from __future__ import annotations


class Solution:
    def dailyTemperatures(self, temperatures: list[int]) -> list[int]:
        n = len(temperatures)
        answer = [0] * n  # default 0: no warmer day found
        unresolved = []  # indices still waiting for a warmer day (temps strictly decreasing)
        for i, temp in enumerate(temperatures):
            while unresolved and temp > temperatures[unresolved[-1]]:
                j = unresolved.pop()
                answer[j] = i - j  # i is j's first strictly warmer day
            unresolved.append(i)
        return answer  # indices left on the stack keep their 0
