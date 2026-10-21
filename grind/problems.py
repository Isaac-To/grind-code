"""Per-problem practice environment: bundled problem data, scaffold rendering,
and the test runner.

problems.json (built offline by scripts/build_problems.py from LeetCode's
published examples) provides, per slug: the rendered statement, the real
starter code, pre-parsed example tests, and comparison semantics the examples
alone can't express (unordered outputs, in-place mutation, value-of-node
results, float tolerance).

TESTS in a scaffold stays plain Python the user can edit:
  call mode:  ((arg, ...), want)                  — one method call
  ops mode:   {"ops": [...], "args": [...], "want": [...]} — design problems
Node-typed arguments are written as the arrays LeetCode prints; the runner
converts them via the module's own ListNode/TreeNode/Node classes, guided by
the method's type annotations.
"""
from __future__ import annotations

import ast
import json
import re
from collections import Counter
from inspect import signature
from pathlib import Path

PROBLEMS_PATH = Path(__file__).parent / "problems.json"
_cache: dict | None = None


def _data() -> dict:
    global _cache
    if _cache is None:
        _cache = json.loads(PROBLEMS_PATH.read_text()) if PROBLEMS_PATH.exists() else {}
    return _cache


def get(slug: str) -> dict | None:
    """Dataset entry for a slug, or None when the problem has no bundled data."""
    return _data().get(slug)


def sem(slug: str) -> dict:
    return (get(slug) or {}).get("sem", {})


# ------------------------------------------------------------ rendering

TYPING = ["List", "Optional", "Dict", "Set", "Tuple", "Union", "Callable",
          "DefaultDict", "Deque", "Iterable", "Any", "Generator"]
COLLECTIONS = ["Counter", "defaultdict", "deque", "OrderedDict"]
MODULES = ["heapq", "bisect", "math", "itertools", "functools", "string"]

LISTNODE_DEF = '''class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
'''

TREENODE_DEF = '''class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
'''

NODE_DEF = '''class Node:
    def __init__(self, x, next=None, random=None):
        self.val = x
        self.next = next
        self.random = random
'''


def _imports(code: str) -> str:
    """Imports the starter code needs — detected, not hardcoded per problem."""
    lines = []
    t = [n for n in TYPING if re.search(rf"\b{n}\b", code)]
    if t:
        lines.append(f"from typing import {', '.join(sorted(t))}")
    c = [n for n in COLLECTIONS if re.search(rf"\b{n}\b", code)]
    if c:
        lines.append(f"from collections import {', '.join(sorted(c))}")
    for m in MODULES:
        if re.search(rf"\b{m}\b", code):
            lines.append(f"import {m}")
    return "\n".join(lines)


def _defined_classes(code: str) -> set[str]:
    """Names of classes the snippet really defines. LeetCode ships node
    classes *commented out* or inside a docstring — those don't count."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return set()
    return {n.name for n in tree.body if isinstance(n, ast.ClassDef)}


def _helpers(code: str) -> str:
    out = []
    defined = _defined_classes(code)
    if re.search(r"\bListNode\b", code) and "ListNode" not in defined:
        out.append(LISTNODE_DEF)
    if re.search(r"\bTreeNode\b", code) and "TreeNode" not in defined:
        out.append(TREENODE_DEF)
    if re.search(r"\bNode\b", code) and "Node" not in defined:
        out.append(NODE_DEF)
    return "\n\n".join(out)


def render_md(prob: dict, entry: dict, target: float, phase: str) -> str:
    """Sidecar solutions/<slug>.md — the statement, fully offline."""
    return (f"# {prob['num']}. {prob['title']}\n\n"
            f"**{prob['difficulty']}** · {prob['topic']} · "
            f"[problem on LeetCode](https://leetcode.com/problems/{prob['slug']}/)\n"
            f"Fluency target: {target:g} min ({phase})\n\n---\n\n"
            f"{entry['markdown'].strip()}\n\n---\n\n"
            "*The examples above are pre-loaded into `TESTS` in the solution file —\n"
            "`grind check` runs a few, `grind done` runs all of them and grades.*\n")


def _fmt_tests(tests: list, mode: str) -> str:
    lines = []
    for t in tests:
        if "ops" in t:
            lines.append(f'    {{"ops": {t["ops"]!r}, "args": {t["args"]!r}, "want": {t["want"]!r}}},')
        else:
            lines.append(f"    ({tuple(t['args'])!r}, {t['want']!r}),")
    body = "\n".join(lines) or "    # no examples parsed — add your own ((args...), expected)"
    return f"TESTS = [\n{body}\n]"


def render_py(prob: dict, entry: dict, target: float, phase: str) -> str:
    """The solution scaffold: real signature, needed imports/helpers,
    pre-filled TESTS. Written once; never overwritten afterwards."""
    code = entry["python"].rstrip()
    head = (f'"""\n{prob["num"]}. {prob["title"]}  [{prob["difficulty"]}]  '
            f'({prob["topic"]})\n\n'
            f"https://leetcode.com/problems/{prob['slug']}/\n"
            f"Statement: {prob['slug']}.md   ·   Fluency target: {target:g} min ({phase})\n"
            '"""\n')
    parts = [p for p in [_imports(code), _helpers(code)] if p]
    parts.append(code)
    parts.append(_fmt_tests(entry["tests"], entry["mode"]))
    return head + "\n\n" + "\n\n".join(parts) + "\n"

# ---------------------------------------------------------- node conversions

def to_linked(vals, cls):
    head = cur = None
    for v in vals or []:
        n = cls(v)
        if head is None:
            head = cur = n
        else:
            cur.next = n
            cur = n
    return head


def from_linked(node) -> list:
    out = []
    while node is not None:
        out.append(node.val)
        node = node.next
    return out


def to_tree(arr, cls):
    vals = list(arr or [])
    if not vals:
        return None
    root = cls(vals[0])
    q, i = [root], 1
    while q and i < len(vals):
        n = q.pop(0)
        for side in ("left", "right"):
            if i < len(vals):
                v = vals[i]
                i += 1
                if v is not None:
                    child = cls(v)
                    setattr(n, side, child)
                    q.append(child)
    return root


def from_tree(root) -> list:
    out, q = [], [root]
    while q:
        n = q.pop(0)
        if n is None:
            out.append(None)
            continue
        out.append(n.val)
        q.append(n.left)
        q.append(n.right)
    while out and out[-1] is None:
        out.pop()
    return out


def to_random_list(vals, cls):
    """[[val, random_index|null], ...] -> linked list with .random pointers."""
    nodes = [cls(v[0]) for v in vals or []]
    for n, v in zip(nodes, vals):
        ri = v[1]
        n.random = nodes[ri] if ri is not None else None
        if ri is not None and ri >= len(nodes):
            raise ValueError("bad random index")
    for a, b in zip(nodes, nodes[1:]):
        a.next = b
    return nodes[0] if nodes else None


def from_random_list(node) -> list:
    nodes, idx = [], {}
    cur = node
    while cur is not None:
        idx[id(cur)] = len(nodes)
        nodes.append(cur)
        cur = cur.next
    return [[n.val, idx.get(id(n.random))] for n in nodes]


def to_graph(adj, cls):
    """Adjacency list [[neighbors of node 1], ...] -> Node 1 of the graph."""
    nodes = [cls(i + 1) for i in range(len(adj or []))]
    for n, neigh in zip(nodes, adj or []):
        n.neighbors = [nodes[j - 1] for j in neigh]
    return nodes[0] if nodes else None


def from_graph(node) -> list:
    """Graph node -> adjacency list, nodes sorted by val (LeetCode's display)."""
    seen: dict[int, object] = {}

    def visit(n):
        if n is None or id(n) in seen:
            return
        seen[id(n)] = n
        for nb in getattr(n, "neighbors", []):
            visit(nb)

    visit(node)
    nodes = sorted(seen.values(), key=lambda x: x.val)
    idx = {id(n): i + 1 for i, n in enumerate(nodes)}
    return [[idx[id(nb)] for nb in n.neighbors] for n in nodes]


def _is_random_node(cls) -> bool:
    """True when the module's Node class carries .random (LC 138); the
    graph flavour (LC 133) has .neighbors and must not be list-linked."""
    try:
        return "random" in signature(cls.__init__).parameters
    except (TypeError, ValueError):
        return False


def _anno(fn, i: int) -> str:
    """Annotation of the i-th real argument (self skipped when present)."""
    try:
        params = [p for p in signature(fn).parameters.values() if p.name != "self"]
        return str(params[i].annotation) if i < len(params) else ""
    except (TypeError, ValueError):
        return ""


def _convert_arg(fn, i, val, mod):
    a = _anno(fn, i)
    if "ListNode" in a:
        return to_linked(val, mod.ListNode) if isinstance(val, list) else mod.ListNode(val)
    if "TreeNode" in a:
        return to_tree(val, mod.TreeNode) if isinstance(val, list) else mod.TreeNode(val)
    if re.search(r"\bNode\b", a) and "ListNode" not in a \
            and hasattr(mod, "Node") and _is_random_node(mod.Node):
        if isinstance(val, list):
            return to_random_list(val, mod.Node)
        return mod.Node(val)
    return val


def _convert_out(fn, got, mod):
    """Method result -> the value LeetCode would print. Node types become
    arrays (an empty/None result prints as []); annotation first, shape after."""
    a = str(signature(fn).return_annotation) if fn else ""
    if isinstance(got, list):
        return got
    if "ListNode" in a:
        return from_linked(got)
    if "TreeNode" in a:
        return from_tree(got)
    if re.search(r"\bNode\b", a) and "ListNode" not in a \
            and hasattr(mod, "Node") and _is_random_node(mod.Node):
        return from_random_list(got)
    if got is None or isinstance(got, (bool, int, float, str)):
        return got
    # un-annotated node returns: best effort by shape
    if hasattr(got, "val") and hasattr(got, "next") and not hasattr(got, "right"):
        return from_linked(got)
    if hasattr(got, "val") and hasattr(got, "right"):
        return from_tree(got)
    return got


# ---------------------------------------------------------------- comparison

def _canon(row, inner: bool):
    if inner and isinstance(row, (list, tuple)):
        return sorted(repr(x) for x in row)
    return repr(row)


def equal(got, want, sem: dict) -> bool:
    """Loose equality with per-problem semantics. Lists compare by value."""
    if sem.get("float") and isinstance(got, (int, float)) and isinstance(want, (int, float)) \
            and not isinstance(got, bool) and not isinstance(want, bool):
        return abs(got - want) <= 1e-5 * max(1.0, abs(want))
    if sem.get("unordered") and isinstance(got, list) and isinstance(want, list):
        g = sorted(_canon(r, sem.get("unordered_inner")) for r in got)
        w = sorted(_canon(r, sem.get("unordered_inner")) for r in want)
        return g == w
    if isinstance(got, (list, tuple)) and isinstance(want, (list, tuple)):
        return list(got) == list(want)
    return got == want


# --------------------------------------------------------------------- find

def _classes(mod) -> list:
    """Top-level classes in the module, in definition order."""
    return [v for v in vars(mod).values()
            if isinstance(v, type) and v.__module__ == mod.__name__]


def _solution_class(mod, prefer: str | None = None):
    classes = _classes(mod)
    by_name = {c.__name__: c for c in classes}
    if prefer and prefer in by_name:
        return by_name[prefer]
    if "Solution" in by_name:
        return by_name["Solution"]
    return classes[-1] if classes else None


def _pick_method(inst, name: str | None):
    """The required method as a *bound* method: the dataset's name when the
    class has it, else the last public method (helpers go above it)."""
    cls = type(inst)
    if name and callable(getattr(inst, name, None)):
        return getattr(inst, name)
    methods = [m for m, v in vars(cls).items() if not m.startswith("_") and callable(v)]
    if not methods:
        raise ValueError(f"no public method found in {cls.__name__}")
    return getattr(inst, methods[-1])


# ------------------------------------------------------------------- runner

def run_tests(mod, tests, slug: str) -> tuple[int, int]:
    """Run scaffold TESTS against the solution. Returns (passed, total);
    prints one line per case, like the old inline runner."""
    s = sem(slug)
    entry = get(slug)
    want_method = entry.get("method") if entry else None
    passed = 0
    for i, t in enumerate(tests, 1):
        try:
            if isinstance(t, dict):
                ok, detail = _run_ops(mod, t, s)
            else:
                ok, detail = _run_call(mod, t, s, want_method)
        except Exception as e:
            ok, detail = False, f"{type(e).__name__}: {e}"
        label = f"[{i}/{len(tests)}]"
        if ok:
            print(f"  {label} ok  {detail}")
        else:
            print(f"  {label} FAIL {detail}")
        passed += ok
    return passed, len(tests)


def _run_call(mod, t, s, want_method):
    argv, want = (list(t[0]) if isinstance(t[0], (list, tuple)) else [t[0]]), t[1]
    inst = _solution_class(mod)()
    fn = _pick_method(inst, want_method)
    if s.get("graph"):
        args = [to_graph(v, mod.Node) if isinstance(v, list) and v and isinstance(v[0], list) else v
                for v in argv]
    else:
        args = [_convert_arg(fn, i, v, mod) for i, v in enumerate(argv)]
    got = fn(*args)
    if s.get("graph"):
        got = from_graph(got)
        return equal(got, want, s), f"args={argv!r} -> {got!r}" + (
            "" if equal(got, want, s) else f"  want {want!r}")
    if "inplace" in s:
        k = s["inplace"]
        a = _anno(fn, k)
        if "ListNode" in a:
            got = from_linked(args[k])
        elif "TreeNode" in a:
            got = from_tree(args[k])
        elif re.search(r"\bNode\b", a) and "ListNode" not in a:
            got = from_random_list(args[k])
        else:
            got = args[k]          # a plain list the method mutated in place
    elif s.get("node_out_value") and hasattr(got, "val"):
        got = got.val
    else:
        got = _convert_out(fn, got, mod)
    if s.get("nqueens"):
        n = argv[0]
        ok = (isinstance(got, list) and len(got) == n and _valid_nqueens(got))
        return ok, f"n={n} -> {got!r}" + ("" if ok else "  want a valid board")
    if s.get("palindromic_substring"):
        src = argv[0] if argv else ""
        ok = (isinstance(got, str) and got in src and got == got[::-1]
              and len(got) == len(want))
        return ok, f"-> {got!r}" + ("" if ok else f"  want a length-{len(want)} palindromic substring of {src!r}")
    ok = equal(got, want, s)
    return ok, f"args={argv!r} -> {got!r}" + ("" if ok else f"  want {want!r}")


def _valid_nqueens(board) -> bool:
    n = len(board)
    if not board or any(len(r) != n or r.count("Q") != 1 for r in board):
        return False
    cols, diag, adiag = set(), set(), set()
    for r in range(n):
        c = board[r].find("Q")
        if c in cols or (r - c) in diag or (r + c) in adiag:
            return False
        cols.add(c)
        diag.add(r - c)
        adiag.add(r + c)
    return True


def _run_ops(mod, t, s):
    ops, arglists, wants = t["ops"], t["args"], t["want"]
    cls = _solution_class(mod, prefer=ops[0])
    cargs = [_convert_arg(cls.__init__, i, v, mod)
             for i, v in enumerate(arglists[0] or [])]
    inst = cls(*cargs)
    prev = None
    for name, argv, want in zip(ops[1:], arglists[1:], wants[1:]):
        m = getattr(inst, name, None)
        if not callable(m):
            return False, f"missing method {name!r}"
        fn = getattr(type(inst), name)
        args = [prev if v == "@prev" else _convert_arg(fn, i, v, mod)
                for i, v in enumerate(argv or [])]
        got = m(*args)
        prev = got
        if want is None or name in s.get("nocheck", []):
            continue
        got = _convert_out(fn, got, mod)
        if not equal(got, want, s):
            return False, f"{name}({', '.join(repr(a) for a in argv)}) -> {got!r}  want {want!r}"
    return True, f"{len(ops) - 1} op(s) ok"
