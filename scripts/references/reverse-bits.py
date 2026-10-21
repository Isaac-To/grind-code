"""Reference solution — 190. Reverse Bits.

Approach: build the answer bit by bit over exactly 32 rounds. In each
round, take the lowest bit of `n` (n & 1) and place it at the position
that mirrors it in a 32-bit word: shift the result left by one and OR
the bit in, then drop that bit from `n` with an unsigned right shift.

Invariant: after k rounds, `result` holds the reversed low k bits of
the original `n` (aligned to the top k of 32 bit positions), and `n`
holds the remaining 32 - k top bits in its low positions. After 32
rounds the whole word has been mirrored.

Complexity: O(1) — always exactly 32 iterations and O(1) space.
"""
from __future__ import annotations


class Solution:
    def reverseBits(self, n: int) -> int:
        result = 0
        for _ in range(32):             # a 32-bit word has exactly 32 positions
            result = (result << 1) | (n & 1)  # append n's lowest bit to the answer
            n >>= 1                     # consume that bit (unsigned shift)
        return result
