"""Reference solution — 371. Sum of Two Integers.

Approach: simulate a binary adder with two bit-parallel operations:
  - `a & b` marks positions where both addends carry in a 1 → a carry
    must propagate to the next bit, so shift it left by one.
  - `a ^ b` is the sum of the bits *ignoring* carries (each position
    becomes 1 iff exactly one addend had a 1 there).
Adding the partial sum and the carry may itself produce new carries,
so loop: the carry's set bits strictly move left (or vanish), and with
Python's unbounded ints we mask both to 32 bits each round to emulate a
fixed-width machine.

Invariant: after each iteration, (partial_sum + carry) mod 2^32 equals
(a + b) mod 2^32 — the pair always sums to the true answer; we stop
when the carry is exhausted.

Why the final sign works: masking to 32 bits makes Python interpret the
word as two's complement. If bit 31 is set, subtracting 2^32 converts
the 32-bit two's-complement pattern to the correct negative value.

Complexity: O(1) — at most 32 carry-propagation rounds for 32-bit
inputs; O(1) space.
"""
from __future__ import annotations

MASK = 0xFFFFFFFF        # keep all values inside a 32-bit word
SIGN_BIT = 0x80000000    # bit 31 — set means "negative" in two's complement


class Solution:
    def getSum(self, a: int, b: int) -> int:
        a &= MASK                       # fold both addends into 32-bit words
        b &= MASK
        while b:                        # a carry is still pending
            carry = ((a & b) << 1) & MASK  # positions that generate a carry
            a = (a ^ b) & MASK          # sum without carries
            b = carry                   # add the carry next round
        # If bit 31 is set, the 32-bit word represents a negative number;
        # subtracting 2^32 converts it to Python's signed value.
        return a - 0x100000000 if a & SIGN_BIT else a
