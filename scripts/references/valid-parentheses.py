"""Reference solution — 20. Valid Parentheses.

Approach: use a stack of currently-open brackets. Scan left to right:
an opening bracket is pushed; a closing bracket must match the most
recently opened one, i.e. the top of the stack, which we pop.

Invariant: the stack holds exactly the open brackets that have not yet
been closed, in order. The string is valid if and only if every close
pops a matching open and the stack is empty at the end.

Two failure modes cover every invalid input:
  - mismatch: a close bracket whose partner is not on top of the stack
    (including an empty stack — a close with nothing open);
  - leftovers: open brackets still on the stack when the string ends.

Trick: map each close bracket to its partner, then "does top match?"
is a single dict lookup plus an equality test.

Complexity: O(n) time — each character is pushed/popped at most once;
O(n) space — worst case all characters are open brackets.
"""
from __future__ import annotations


class Solution:
    def isValid(self, s: str) -> bool:
        # partner for every closing bracket; opens have no entry
        close_to_open = {")": "(", "]": "[", "}": "{"}
        open_brackets = []  # stack of unmatched open brackets
        for ch in s:
            if ch in close_to_open:
                # closing bracket: top of stack must be its partner
                if not open_brackets or open_brackets[-1] != close_to_open[ch]:
                    return False  # nothing open, or wrong bracket type
                open_brackets.pop()  # correctly closed — retire it
            else:
                open_brackets.append(ch)  # opening bracket — wait for its close
        return not open_brackets  # valid only if every open was closed
