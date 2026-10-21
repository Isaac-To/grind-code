"""Reference solution — 125. Valid Palindrome.

Approach: two pointers walking inward from both ends of the string.
Skip any character that is not alphanumeric, compare lowercase forms,
and stop when the pointers meet or cross.

Invariant: at every moment, all characters *outside* the window
(left, right) that were already examined were matched successfully.
So if the loop finishes without a mismatch, the cleaned string is a
palindrome. Because the cleaned string is a palindrome exactly when
its reversed half matches, examining each pair once suffices — no
string building, no extra memory.

Note str.isalnum() treats digits and letters (Unicode-aware) as
alphanumeric, and str.lower() normalizes case, which is exactly the
"clean then compare" rule the problem asks for.

Complexity: O(n) time — each pointer traverses the string at most
once; O(1) space — only two indices are stored.
"""
from __future__ import annotations


class Solution:
    def isPalindrome(self, s: str) -> bool:
        left, right = 0, len(s) - 1  # two pointers, inclusive ends
        while left < right:         # pointers not yet met/crossed
            # Advance left past punctuation, spaces, symbols, ...
            while left < right and not s[left].isalnum():
                left += 1
            # ...and right likewise.
            while left < right and not s[right].isalnum():
                right -= 1
            if s[left].lower() != s[right].lower():
                return False        # mismatched pair -> not a palindrome
            left += 1               # pair matched; shrink the window
            right -= 1
        return True                 # every pair matched (or empty/singleton)
