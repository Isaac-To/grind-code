"""grind.problems — bundled problem data, scaffold rendering, and the runner.

Covers the per-problem practice environment end-to-end: every bank problem
must render an importable scaffold with pre-parsed TESTS, and reference
solutions across every runner family must pass (a wrong one must fail).

Reference solutions are injected under the *scaffold's own* signatures —
exactly how a real user works (the body replaces the `pass` placeholder)."""
from __future__ import annotations

import types
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from grind import problems
from grind.scheduler import bank


def _import_source(name: str, src: str):
    mod = type(sys)(f"grind_test_{name}")       # a fresh module, no bytecode cache
    mod.__file__ = f"<{name}>"
    exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    return mod


def _inject_body(src: str, method: str, body: str) -> str:
    """Replace the placeholder under `def method(...)` with real code. The
    placeholder is the `pass` line normalize adds, or the "Do not return..."
    docstring some snippets carry instead."""
    lines = src.split("\n")
    out: list[str] = []
    i, done = 0, False
    while i < len(lines):
        ln = lines[i]
        out.append(ln)
        if not done and re.match(rf"\s*def {method}\(", ln):
            while not ln.rstrip().endswith(":"):        # multi-line signature
                i += 1
                ln = lines[i]
                out.append(ln)
            i += 1
            if i < len(lines) and lines[i].strip().startswith('"""'):
                if lines[i].strip().endswith('"""') and len(lines[i].strip()) > 3:
                    i += 1                             # single-line docstring
                else:
                    i += 1                             # past the opening
                    while not lines[i].strip().endswith('"""'):
                        i += 1
                    i += 1                             # past the closing
            elif i < len(lines) and lines[i].strip() == "pass":
                i += 1                                 # replace the pass
            indent = re.match(r"\s*", lines[max(i - 1, 0)]).group(0)
            assert body.split("\n")[0].startswith(indent), \
                f"body for {method} must be indented at method level"
            out.extend(body.split("\n"))
            done = True
        i += 1
    assert done, f"no placeholder found for {method}"
    return "\n".join(out)

def build_solved_module(slug: str, bodies: dict[str, str]):
    prob = next(p for p in bank() if p["slug"] == slug)
    entry = problems.get(slug)
    assert entry, f"no dataset entry for {slug}"
    scaffold = problems.render_py(prob, entry, 15, "prior")
    for method, body in bodies.items():
        scaffold = _inject_body(scaffold, method, body)
    return _import_source(slug.replace("-", "_"), scaffold), entry


def run_reference(slug: str, bodies: dict[str, str]) -> tuple[int, int]:
    mod, _ = build_solved_module(slug, bodies)
    return problems.run_tests(mod, mod.TESTS, slug)


# --------------------------------------------------------- dataset integrity

def test_every_bank_problem_has_environment():
    missing = [p["slug"] for p in bank() if problems.get(p["slug"]) is None]
    assert missing == []


def test_every_scaffold_renders_importable_with_tests():
    for p in bank():
        entry = problems.get(p["slug"])
        mod = _import_source("scaffold_" + p["slug"].replace("-", "_"),
                             problems.render_py(p, entry, 15, "prior"))
        assert getattr(mod, "TESTS"), f"empty TESTS in {p['slug']}"
        if entry["mode"] == "call":
            assert entry["method"], f"no method recorded for {p['slug']}"
        assert entry["markdown"].strip(), f"no statement for {p['slug']}"


def test_statement_markdown_carries_examples_and_constraints():
    entry = problems.get("two-sum")
    assert "Example" in entry["markdown"]
    assert "Constraints" in entry["markdown"]


def test_scaffold_has_real_signature_helpers_and_tests():
    prob = next(p for p in bank() if p["slug"] == "add-two-numbers")
    src = problems.render_py(prob, problems.get("add-two-numbers"), 15, "prior")
    assert "def addTwoNumbers(self, l1" in src          # real LeetCode signature
    assert re.search(r"^class ListNode:", src, re.M)     # helper class emitted
    assert "TESTS = [" in src and "(([" in src           # examples pre-filled


# --------------------------------------------------- reference solutions

REF = {
    "two-sum": {"twoSum": """        seen = {}
        for i, x in enumerate(nums):
            if target - x in seen:
                return [seen[target - x], i]
            seen[x] = i"""},
    "add-two-numbers": {"addTwoNumbers": """        dummy = cur = ListNode()
        carry = 0
        while l1 or l2 or carry:
            s = (l1.val if l1 else 0) + (l2.val if l2 else 0) + carry
            carry, d = divmod(s, 10)
            cur.next = ListNode(d)
            cur = cur.next
            l1 = l1.next if l1 else None
            l2 = l2.next if l2 else None
        return dummy.next"""},
    "invert-binary-tree": {"invertTree": """        if root:
            root.left, root.right = self.invertTree(root.right), self.invertTree(root.left)
        return root"""},
    "rotate-image": {"rotate": """        n = len(matrix)
        for i in range(n):
            for j in range(i + 1, n):
                matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
        for row in matrix:
            row.reverse()"""},
    "subsets": {"subsets": """        n = len(nums)
        return [[nums[i] for i in range(n) if mask >> i & 1] for mask in range(1 << n)]"""},
    "min-stack": {
        "push": "        self.st.append((value, min(value, self.st[-1][1] if self.st else value)))",
        "pop": "        self.st.pop()",
        "top": "        return self.st[-1][0]",
        "getMin": "        return self.st[-1][1]",
        "__init__": "        self.st = []",
    },
    "kth-largest-element-in-a-stream": {
        "__init__": "        self.k, self.arr = k, sorted(nums)",
        "add": """        import bisect
        bisect.insort(self.arr, val)
        return self.arr[-self.k]""",
    },
    "clone-graph": {"cloneGraph": """        if not node:
            return None
        made = {}
        def go(n):
            if n in made:
                return made[n]
            c = Node(n.val)
            made[n] = c
            c.neighbors = [go(x) for x in n.neighbors]
            return c
        return go(node)"""},
    "n-queens": {"solveNQueens": """        cols, diag, ad = set(), set(), set()
        board = []
        def go(r):
            if r == n:
                return True
            for c in range(n):
                if c in cols or r - c in diag or r + c in ad:
                    continue
                cols.add(c); diag.add(r - c); ad.add(r + c)
                board.append('.' * c + 'Q' + '.' * (n - c - 1))
                if go(r + 1):
                    return True
                board.pop()
                cols.remove(c); diag.remove(r - c); ad.remove(r + c)
            return False
        go(0)
        return board"""},
    "powx-n": {"myPow": """        if n < 0:
            x, n = 1 / x, -n
        out = 1.0
        while n:
            if n & 1:
                out *= x
            x *= x
            n >>= 1
        return out"""},
}


@pytest.mark.parametrize("slug", sorted(REF))
def test_reference_solution_passes(slug):
    passed, total = run_reference(slug, REF[slug])
    assert passed == total, f"{slug}: {passed}/{total}"


def test_wrong_solution_fails():
    bodies = {"twoSum": REF["two-sum"]["twoSum"].replace("target - x", "target + x")}
    passed, total = run_reference("two-sum", bodies)
    assert passed < total


def test_unordered_accepts_any_row_order():
    mod, _ = build_solved_module("subsets", REF["subsets"])
    argv, want = list(mod.TESTS[0][0]), mod.TESTS[0][1]
    mod.TESTS = [(argv, list(reversed(want)))]  # a valid but reordered answer
    passed, total = problems.run_tests(mod, mod.TESTS, "subsets")
    assert passed == total


def test_ops_mode_instantiates_named_class_and_skips_null_wants():
    # MinStack: ops sequence runs against the class named by the first op;
    # null wants (constructor/void ops) are skipped, real values compared
    passed, total = run_reference("min-stack", REF["min-stack"])
    assert passed == total
    passed, total = run_reference("kth-largest-element-in-a-stream",
                                  REF["kth-largest-element-in-a-stream"])
    assert passed == total


def test_inplace_compares_mutated_argument():
    passed, total = run_reference("rotate-image", REF["rotate-image"])
    assert passed == total


def test_nqueens_accepts_any_valid_board():
    body = REF["n-queens"]["solveNQueens"].replace(
        "for c in range(n):", "for c in reversed(range(n)):")
    passed, total = run_reference("n-queens", {"solveNQueens": body})
    assert passed == total


def test_float_tolerance():
    passed, total = run_reference("powx-n", REF["powx-n"])
    assert passed == total
