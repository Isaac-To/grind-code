"""Reference solution — 2013. Detect Squares.

Approach: keep a Counter of added points. To count squares with the query
point (px, py) as one corner, iterate over every *added* point (x, y) and
treat it as the diagonally opposite corner. A square's diagonal is at 45
degrees to the axes, so the pair forms a valid diagonal exactly when
|x - px| == |y - py| and both are non-zero. The other two corners are then
forced: (x, py) and (px, y). Multiply the counts of the three points.

Why it works: every axis-aligned square is determined uniquely by one
diagonal, and counting by diagonal pairs counts each square exactly once
(choosing the anti-diagonal corner of the same square would give a
different diagonal — the square's *other* diagonal — which produces the
same three points, so each square is counted once per diagonal choice
made consistently). The Counter handles duplicate points for free:
multiplicities of the diagonal and the two flanking corners combine to
the number of point-triples forming squares.

Invariant: `points` always reflects exactly the multiset of added points,
so `count` only needs local geometry around the query.

Complexity: add O(1); count O(P) where P is the number of distinct added
points (at most 3000 total calls, well within limits); space O(P).
"""
from __future__ import annotations

from collections import Counter


class DetectSquares:
    def __init__(self):
        # Multiset of added points: maps (x, y) -> number of copies.
        self.points: Counter[tuple[int, int]] = Counter()

    def add(self, point: list[int]) -> None:
        self.points[tuple(point)] += 1

    def count(self, point: list[int]) -> int:
        px, py = point
        total = 0
        for (x, y), copies in self.points.items():
            # Candidate diagonal corner: needs equal, non-zero axis distances.
            side = abs(x - px)
            if side == 0 or side != abs(y - py):
                continue  # same point, collinear, or a rectangle not a square
            # The two remaining corners are forced by the diagonal.
            total += copies * self.points[(x, py)] * self.points[(px, y)]
        return total
