"""Reference solution — 43. Multiply Strings.

Approach: grade-school long multiplication, digit by digit, without ever
converting the whole strings to integers. Key fact: multiplying the digit
at index i of num1 by the digit at index j of num2 contributes to exactly
one cell of the result array — position i + j + 1 (0-based, in a length
m+n array), because a number with d digits times one with e digits has at
most d+e digits.

Invariant: after processing digit pairs up to (i, j), cell i+j+1 of
`cells` holds the total (mod 10, with carry pushed left) of all processed
products landing there. Carries never collide because we push overflow
leftward immediately, and the leftmost cell (index 0) can absorb the final
carry with room to spare — max product of two 200-digit numbers fits in
400 digits.

Complexity: O(m*n) time for the digit-pair sweep, O(m+n) for the carry
fix-up; O(m+n) extra space for the cells array.
"""
from __future__ import annotations


class Solution:
    def multiply(self, num1: str, num2: str) -> str:
        # A string of one or more zeros always yields "0".
        if num1 == "0" or num2 == "0":
            return "0"

        m, n = len(num1), len(num2)
        # cells[k] will hold the k-th digit (leftmost is index 0) of the product.
        cells = [0] * (m + n)

        # Multiply every digit pair, accumulating into the landing cell.
        # num1[i] * num2[j] lands in position i + j + 1.
        for i in range(m - 1, -1, -1):
            for j in range(n - 1, -1, -1):
                product = (ord(num1[i]) - ord("0")) * (ord(num2[j]) - ord("0"))
                pos = i + j + 1
                total = product + cells[pos]        # add what already sits here
                cells[pos] = total % 10             # digit that stays
                cells[pos - 1] += total // 10       # carry pushed one cell left

        # cells[0] may have grown past 9 after the final carries — normalize.
        for k in range(m + n - 1, 0, -1):
            carry, cells[k] = divmod(cells[k], 10)
            cells[k - 1] += carry

        # Drop the single possible leading zero (products of unequal lengths).
        start = 0
        while start < len(cells) - 1 and cells[start] == 0:
            start += 1
        return "".join(str(d) for d in cells[start:])
