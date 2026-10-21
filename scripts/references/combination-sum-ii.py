"""Reference solution — 40. Combination Sum II.

Approach: sort the candidates, then DFS with a per-level skip rule for
duplicates. Each candidate may be used at most once, so the recursion moves
to index i + 1 after choosing candidate i. The duplicate hazard: equal
values sitting at consecutive indices would produce identical combinations.
Rule: within one loop iteration, if candidates[i] == candidates[i - 1] and
i > start, skip it — that value has already anchored a branch at this level,
so starting another branch with the same value would repeat work. Using a
value *later* in the path (when i == start) is fine, which is exactly how
combinations like [1, 1, 6] arise.

Invariant: after sorting, every complete combination is emitted in
nondecreasing order, and the skip rule admits at most one branch per
distinct value per tree level — hence no duplicate combinations.

Complexity: O(2^n) nodes in the worst case (n <= 100 but target <= 30 prunes
hard); O(n) recursion depth.
"""
from __future__ import annotations


class Solution:
    def combinationSum2(self, candidates: list[int], target: int) -> list[list[int]]:
        candidates = sorted(candidates)  # group equal values; enables pruning
        result: list[list[int]] = []

        def dfs(start: int, remaining: int, path: list[int]) -> None:
            if remaining == 0:
                result.append(path[:])  # exact sum reached
                return
            for i in range(start, len(candidates)):
                c = candidates[i]
                if c > remaining:
                    break  # sorted: all later candidates exceed the remainder
                if i > start and c == candidates[i - 1]:
                    continue  # same value already anchored this level — skip
                path.append(c)
                dfs(i + 1, remaining - c, path)  # i + 1: each value used once
                path.pop()  # backtrack

        dfs(0, target, [])
        return result
