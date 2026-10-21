"""Reference solution — 191. Number of 1 Bits.

Approach: peel off the lowest set bit repeatedly with the trick
`n & (n - 1)`, which clears exactly the lowest set bit of `n`.
Count how many times we can do that before `n` reaches 0; each step
removes precisely one set bit.

Why `n & (n - 1)` clears the lowest set bit: subtracting 1 flips the
lowest set bit to 0 and every 0 below it to 1, so AND-ing with the
original zeroes that bit (and its trailing zeros) while leaving all
higher bits untouched.

Invariant: each loop iteration removes exactly one set bit, so the loop
runs exactly `popcount(n)` times.

Complexity: O(k) time where k is the number of set bits (<= 32);
O(1) space.
"""
from __future__ import annotations


class Solution:
    def hammingWeight(self, n: int) -> int:
        count = 0
        while n:                        # a set bit remains
            n &= n - 1                  # clear the lowest set bit
            count += 1                  # ...so count it
        return count
