"""Reference solution — 7. Reverse Integer.

Approach: work digit by digit with pure arithmetic (no string
conversion, so no big-int materialization of the reversed value).
Each round: pop the last digit with `x % 10`, push it onto `rev` with
`rev * 10 + digit`, then drop it from `x` with `x // 10`. To keep the
digit math clean we reverse |x| and re-apply the sign afterward.

Invariant: `rev` is always the reverse of the digits consumed so far,
so checking it against INT_MAX // 10 *before* pushing the next digit
catches overflow before it happens.

Complexity: O(log|x|) time — one iteration per digit; O(1) space.
"""
from __future__ import annotations

INT_MAX = 2 ** 31 - 1   #  2147483647, largest signed 32-bit int
INT_MIN = -(2 ** 31)     # -2147483648, smallest signed 32-bit int


class Solution:
    def reverse(self, x: int) -> int:
        sign = -1 if x < 0 else 1
        x = abs(x)                      # reverse the magnitude; sign handled separately
        rev = 0
        while x:
            digit = x % 10              # pop the last digit
            x //= 10
            # Overflow guard: rev * 10 + digit must stay within INT_MAX.
            if rev > INT_MAX // 10 or (rev == INT_MAX // 10 and digit > 7):
                return 0                # would overflow the signed 32-bit range
            rev = rev * 10 + digit      # push the digit on
        rev *= sign
        return rev if INT_MIN <= rev <= INT_MAX else 0
