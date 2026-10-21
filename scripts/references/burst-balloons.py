"""Reference solution — 312. Burst Balloons.

Approach: interval DP on the reverse question. Directly thinking about
WHICH balloon to burst first is messy (the neighbours change), so instead
decide which balloon bursts LAST inside each window.

Pad nums with a virtual 1 on each side: balloons[-1..n] = [1] + nums + [1].
Define dp[l][r] = max coins collectible by bursting exactly the open
balloons strictly between walls l and r (both walls stay intact while the
inside bursts).

For each choice k of the LAST balloon to burst in (l, r):
    dp[l][r] = max over l < k < r of
        dp[l][k] + nums[k] * nums[l] * nums[r] + dp[k][r]
When k bursts last, everything in (l, k) and (k, r) is already gone, so
k's neighbours are the walls l and r — known constants! That is the whole
trick: choosing the LAST burst freezes the neighbour product.

Invariant: dp[l][r] only depends on strictly narrower intervals, so fill
by increasing window width. The answer is dp[0][n+1]: burst everything
between the two virtual 1s.

Base case: width-2 windows have no interior balloons — dp = 0.

Complexity: O(n^3) time (three nested loops over width/l/k), O(n^2) space.
"""
from __future__ import annotations


class Solution:
    def maxCoins(self, nums: list[int]) -> int:
        balloons = [1] + nums + [1]         # virtual walls worth 1 coin each
        n = len(balloons)
        # dp[l][r]: best coins bursting all balloons strictly inside (l, r)
        dp = [[0] * n for _ in range(n)]
        for width in range(2, n):           # distance between the walls
            for l in range(n - width):
                r = l + width
                best = 0
                for k in range(l + 1, r):    # k bursts LAST in this window
                    gain = (
                        dp[l][k]                      # inside-left done earlier
                        + balloons[k] * balloons[l] * balloons[r]
                        + dp[k][r]                    # inside-right done earlier
                    )
                    best = max(best, gain)
                dp[l][r] = best
        return dp[0][n - 1]                 # everything between the two 1s
