"""Reference solution — 136. Single Number.

Approach: XOR every element together. XOR is its own inverse
(a ^ a = 0) and 0 is the identity (a ^ 0 = a), so every element that
appears twice cancels itself out, leaving only the single element.

Invariant: after processing a prefix of the array, `result` holds the XOR
of that prefix. Duplicated values contribute nothing (they pair up and
annihilate), so the final value is exactly the lone single number.

Complexity: O(n) time — one pass; O(1) extra space — a single integer.
"""
from __future__ import annotations


class Solution:
    def singleNumber(self, nums: list[int]) -> int:
        result = 0                      # XOR identity: 0 ^ x == x
        for num in nums:
            result ^= num               # pairs cancel (x ^ x == 0); single survives
        return result
