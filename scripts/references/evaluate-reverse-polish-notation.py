"""Reference solution — 150. Evaluate Reverse Polish Notation.

Approach: a single pass with a stack of intermediate values. Each token
is either a number (push it) or an operator (pop two operands, apply the
operator, push the result).

Invariant: after processing each token the stack holds exactly the
operands/results of all completed sub-expressions; a valid RPN stream
always leaves one value — the answer.

Division subtlety: RPN here truncates toward zero (e.g. -132/10 → -13,
not Python's floor -14). Python's // floors, so for negative operands we
use int(a / b) — true division then truncation — which matches LeetCode.
(A pure-integer equivalent: -(-a // b) when signs differ.)

Complexity: O(n) time — one pass, each token does O(1) stack work;
O(n) space — the stack never holds more than the pending operands.
"""
from __future__ import annotations


class Solution:
    def evalRPN(self, tokens: list[str]) -> int:
        stack = []  # pending operand values

        def divide(a: int, b: int) -> int:
            # truncate toward zero, unlike Python's floor division
            return -(-a // b) if (a < 0) != (b < 0) else a // b

        for token in tokens:
            if token in ("+", "-", "*", "/"):
                b = stack.pop()  # right operand was pushed last
                a = stack.pop()
                if token == "+":
                    stack.append(a + b)
                elif token == "-":
                    stack.append(a - b)
                elif token == "*":
                    stack.append(a * b)
                else:
                    stack.append(divide(a, b))
            else:
                stack.append(int(token))  # negative numbers are also plain ints here
        return stack[-1]  # single remaining value is the expression's value
