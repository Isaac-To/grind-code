"""Reference solution — 74. Search a 2D Matrix.

Approach: the matrix's two guarantees — rows sorted left-to-right and every
row starting after the previous row ends — mean reading the rows in order
gives one fully sorted list of m*n numbers. Instead of flattening (O(m*n)
space) or binary-searching twice, treat the matrix as a virtual sorted array
and binary search it directly: candidate index `mid` maps to the real cell
matrix[mid // n][mid % n], where n is the row width.

Invariant: the closed window [lo, hi] over virtual indices 0..m*n-1 always
contains a virtual index whose cell equals target, if one exists. Each probe
compares the cell at the virtual midpoint against target and discards half
the window, exactly like classic 1-D binary search.

Complexity: O(log(m*n)) time; O(1) space — nothing but three indices.
"""
from __future__ import annotations


class Solution:
    def searchMatrix(self, matrix: list[list[int]], target: int) -> bool:
        rows, cols = len(matrix), len(matrix[0])   # shape of the matrix
        lo, hi = 0, rows * cols - 1                # closed window over virtual indices
        while lo <= hi:                            # window still holds candidates
            mid = (lo + hi) // 2                   # virtual midpoint
            value = matrix[mid // cols][mid % cols]  # map virtual index -> real cell
            if value < target:
                lo = mid + 1                       # target can only be right of mid
            elif value > target:
                hi = mid - 1                       # ...or left of mid
            else:
                return True                        # exact hit
        return False                               # window empty: target absent
