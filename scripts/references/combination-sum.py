"""Reference solution — 39. Combination Sum.

Approach: DFS over the candidates with unlimited reuse. The loop at each
level iterates over candidate indices from `start` onward; recursing with
the *same* index i (not i + 1) is what allows a candidate to be reused.
Restricting the loop to indices >= start keeps every combination generated
in nondecreasing index order, so each multiset of numbers is produced once.

Invariant: `path` sums to exactly (target - remaining), using only
candidates at indices >= the `start` of the current frame. When remaining
hits 0, path sums exactly to target and is recorded. A candidate larger
than remaining can never contribute, so sorting candidates first lets us
break the loop as soon as candidates[i] > remaining.

Complexity: O(n^(T/M)) in the worst case (n candidates, target T, smallest
value M) — the recursion tree has that many nodes; O(T/M) recursion depth.
"""
from __future__ import annotations


class Solution:
    def combinationSum(self, candidates: list[int], target: int) -> list[list[int]]:
        candidates = sorted(candidates)  # enables the early `break` pruning
        result: list[list[int]] = []

        def dfs(start: int, remaining: int, path: list[int]) -> None:
            if remaining == 0:
                result.append(path[:])  # path sums exactly to target — done
                return
            for i in range(start, len(candidates)):
                c = candidates[i]
                if c > remaining:
                    break  # sorted: every later candidate is too big as well
                path.append(c)            # use candidate i once...
                dfs(i, remaining - c, path)  # ...and may reuse it (index i again)
                path.pop()               # backtrack

        dfs(0, target, [])
        return result
