"""Reference solution — 91. Decode Ways.

Approach: scan left to right; dp[i] = number of ways to decode the first i
digits. A decoding's last code is either 1 digit ('1'..'9') or 2 digits
(10..26), so
    dp[i] = (s[i-1] != '0') * dp[i-1] + (10 <= int(s[i-2:i]) <= 26) * dp[i-2].

Invariant: dp[i] counts every decoding of the prefix of length i exactly
once — each decoding's last code has a fixed length (1 or 2), and removing
it leaves a decoding of the shorter prefix, so both recurrences partition
all decodings by their last code without overlap.

Base cases: dp[0] = 1 (the empty prefix decodes one way — do nothing);
dp[1] = 1 iff s[0] is '1'..'9'. Any dp value that becomes 0 propagates
correctly (an unreadable prefix has no decodings): a string starting with
'0', or containing a '0' not preceded by '1'/'2', yields 0.

Complexity: O(n) time, O(1) space (two rolling dp values).
"""
from __future__ import annotations


class Solution:
    def numDecodings(self, s: str) -> int:
        if s[0] == "0":
            return 0                    # no valid first code exists
        prev2, prev1 = 1, 1             # dp[0]=1, dp[1]=1 (s[0] is '1'..'9')
        for i in range(2, len(s) + 1):
            curr = 0
            if s[i - 1] != "0":          # single-digit code '1'..'9'
                curr += prev1
            if s[i - 2] == "1" or (s[i - 2] == "2" and s[i - 1] <= "6"):
                curr += prev2           # two-digit code 10..26
            prev2, prev1 = prev1, curr  # roll the dp window forward
        return prev1
