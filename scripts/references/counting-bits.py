"""Reference solution — 338. Counting Bits.

Approach: dynamic programming on the binary structure of numbers.
For any i, `ans[i]` equals `ans[i >> 1]` plus its lowest bit `i & 1`:
dropping the last bit of i (i >> 1) gives a strictly smaller number
whose popcount we already know, and the last bit contributes 0 or 1.

Invariant: when we compute `ans[i]`, all `ans[j]` for j < i are final,
so `ans[i >> 1]` is trustworthy (i >> 1 < i for i >= 1).

Complexity: O(n) time — one pass with O(1) work per index;
O(n) space for the output array (unavoidable).
"""
from __future__ import annotations


class Solution:
    def countBits(self, n: int) -> list[int]:
        ans = [0] * (n + 1)             # ans[0] = 0: zero has no set bits
        for i in range(1, n + 1):
            ans[i] = ans[i >> 1] + (i & 1)  # popcount(i) = popcount(i//2) + last bit
        return ans
