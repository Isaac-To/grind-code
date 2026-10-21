"""Reference solution — 678. Valid Parenthesis String.

Approach: greedy range tracking. While scanning, keep [lo, hi] — the set of
possible open-parenthesis counts, as a contiguous range:
  - '(' shifts the whole range up by 1
  - ')' shifts it down by 1 (counts below 0 are impossible: clamp lo)
  - '*' branches into all three roles, widening the range by 1 on each side

Invariant: after processing a prefix, the true possible open counts are
exactly the integers in [lo, hi]. A mismatch ')' with lo == 0 kills the
low end only (the '*'s could be '('), tracked by clamping. The string is
valid iff 0 remains possible at the end (lo == 0); if the range ever empties
(lo > hi), every branch has already broken a rule.

Complexity: O(n) time, O(1) space.
"""
from __future__ import annotations


class Solution:
    def checkValidString(self, s: str) -> bool:
        lo = hi = 0                    # possible open-paren counts: [lo, hi]
        for c in s:
            if c == '(':
                lo += 1
                hi += 1
            elif c == ')':
                lo = max(lo - 1, 0)    # negative open count is impossible
                hi -= 1
            else:                      # '*': '(', ')' or empty — widen both ways
                lo = max(lo - 1, 0)
                hi += 1
            if hi < 0:                 # even treating every '*' as '(' fails
                return False
        return lo == 0                 # some branch closes everything
