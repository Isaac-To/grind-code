"""Reference solution — 207. Course Schedule.

Approach: cycle detection with Kahn's topological sort. Build the
prerequisite graph (edge b -> a means "b unlocks a") and count each node's
in-degree. Repeatedly strip nodes with in-degree 0 — courses ready to
take — and unlock their dependents. All courses are finishable iff every
node gets stripped, i.e. the graph has no cycle.

Invariant: a node's in-degree counts the prerequisites not yet taken;
when it hits 0 the course becomes available. If a cycle exists, none of
its members ever reaches in-degree 0, so the stripped count stalls
below numCourses.

Complexity: O(V + E) time — every edge relaxes exactly one in-degree;
O(V + E) space for adjacency lists and the queue.
"""
from __future__ import annotations

from collections import deque


class Solution:
    def canFinish(self, numCourses: int, prerequisites: list[list[int]]) -> bool:
        # adj[b] = courses that become available once b is taken
        adj: list[list[int]] = [[] for _ in range(numCourses)]
        indegree = [0] * numCourses           # unmet prerequisite count per course
        for course, prereq in prerequisites:  # [a, b]: take b before a
            adj[prereq].append(course)
            indegree[course] += 1

        # start with every course whose prerequisites are already satisfied
        queue = deque(i for i in range(numCourses) if indegree[i] == 0)
        taken = 0
        while queue:
            cur = queue.popleft()
            taken += 1
            for nxt in adj[cur]:              # taking cur satisfies one prereq of nxt
                indegree[nxt] -= 1
                if indegree[nxt] == 0:        # all prereqs met -> ready
                    queue.append(nxt)

        return taken == numCourses           # a cycle would leave nodes unstripped
