"""Reference solution — 155. Min Stack.

Approach: keep two stacks — the values themselves, and, in lockstep, the
minimum of the values stack as seen at each depth. push(x) appends x and
also min(x, previous min); pop() drops the top of both; getMin() just
reads the top of the min stack.

Invariant: after any sequence of pushes, min_stack[k] is the minimum of
value_stack[0..k]. Because each push records the minimum *at that depth*,
popping automatically restores the previous minimum — no rescan needed.

Complexity: O(1) time per operation (the problem's requirement);
O(n) space — the min stack doubles the storage.
"""
from __future__ import annotations


class MinStack:
    def __init__(self):
        self.values = []   # the actual stack contents
        self.mins = []     # mins[k] = min of values[0..k]

    def push(self, value: int) -> None:
        # new running min is value itself if smaller than the old min
        # (or if the stack was empty)
        new_min = value if not self.mins or value < self.mins[-1] else self.mins[-1]
        self.values.append(value)
        self.mins.append(new_min)  # record the min *at this depth*

    def pop(self) -> None:
        self.values.pop()
        self.mins.pop()  # dropping the depth also drops its min — old min is restored

    def top(self) -> int:
        return self.values[-1]

    def getMin(self) -> int:
        return self.mins[-1]  # minimum among everything currently pushed
