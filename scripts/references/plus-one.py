"""Reference solution — 66. Plus One.

Approach: schoolbook addition of 1, done from the least significant digit.
Walk right-to-left propagating a carry: if the current digit is 9 it
becomes 0 and the carry survives; any other digit just increments and we
are done. If the loop finishes without dying, every digit was 9 — prepend 1
(e.g. 999 -> 1000).

Invariant: at each step, `digits` represents the original number plus 1,
modulo the still-unprocessed higher digits. The early return fires the
moment no carry remains, so no unnecessary work is done past the first
non-9 digit.

Complexity: O(n) time in the worst case (all nines), usually O(1) for the
common case; O(n) space only when a new leading digit must be inserted
(the returned list), O(1) otherwise (in-place digit updates).
"""
from __future__ import annotations


class Solution:
    def plusOne(self, digits: list[int]) -> list[int]:
        # Scan from least significant (rightmost) digit to most significant.
        for i in range(len(digits) - 1, -1, -1):
            if digits[i] == 9:
                digits[i] = 0       # 9 + 1 = 10 -> write 0, carry continues
            else:
                digits[i] += 1      # carry absorbed here — addition complete
                return digits

        # Every digit was 9 (e.g. 999 -> 1000): all digits are now 0,
        # so a leading 1 must be inserted.
        return [1] + digits
