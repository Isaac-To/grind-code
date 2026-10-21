"""Reference solution — 50. Pow(x, n).

Approach: exponentiation by squaring. x^n splits by the parity of n:
  x^n = (x^(n//2))^2         if n is even
  x^n = (x^(n//2))^2 * x     if n is odd
Halve the exponent recursively; square the result on the way back up and
multiply in one extra x for each odd exponent encountered. Negative exponents
use x^(-n) = 1 / x^n.

Why it works: invariant on the recursion — `power(k)` correctly returns
x^k for every k it is called with, and each call halves k, so the exponent
reaches the base case 0 (x^0 = 1) after O(log |n|) halvings. Squaring the
half-exponent result doubles the exponent exactly, so the pieces recombine
to the original n. Iterative form: the low bit of n tells whether the
current square of x belongs in the answer.

Complexity: O(log |n|) time — the exponent halves each level;
O(1) extra space (iterative version holds only two variables).
"""
from __future__ import annotations


class Solution:
    def myPow(self, x: float, n: int) -> float:
        # Work with a non-negative exponent; flip at the end for n < 0.
        exponent = abs(n)
        result = 1.0
        base = x

        # Iterative squaring: consume exponent bit by bit.
        while exponent > 0:
            if exponent & 1:          # current lowest bit is set:
                result *= base       # this power of x belongs in the answer
            base *= base             # x -> x^2 -> x^4 -> x^8 ...
            exponent >>= 1           # halve the remaining exponent
        return result if n >= 0 else 1.0 / result
