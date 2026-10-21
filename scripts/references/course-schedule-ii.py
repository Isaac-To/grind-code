"""Reference solution — 210. Course Schedule II.

Approach: Kahn's topological sort. Edges run prerequisite -> dependent;
nodes with in-degree 0 have all prerequisites done. Stripping ready
nodes in queue order produces a valid order. If a cycle exists the
queue stalls before all courses appear, and we return [].

Invariant: a course is appended to `order` only after every one of its
prerequisites already appears earlier in `order` — exactly the
topological property. Any valid order is accepted (sem: unordered).

Complexity: O(V + E) time; O(V + E) space.
"""
from __future__ import annotations

from collections import deque


class Solution:
    def findOrder(self, numCourses: int, prerequisites: list[list[int]]) -> list[int]:
        adj: list[list[int]] = [[] for _ in range(numCourses)]
        indegree = [0] * numCourses
        for course, prereq in prerequisites:  # [a, b]: b must precede a
            adj[prereq].append(course)
            indegree[course] += 1

        queue = deque(i for i in range(numCourses) if indegree[i] == 0)
        order: list[int] = []
        while queue:
            cur = queue.popleft()
            order.append(cur)                 # all prereqs already in `order`
            for nxt in adj[cur]:
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    queue.append(nxt)

        return order if len(order) == numCourses else []  # [] signals a cycle
