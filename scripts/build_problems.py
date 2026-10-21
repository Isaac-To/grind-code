#!/usr/bin/env python3
"""Build grind/problems.json from scripts/raw_problems.json.

Per slug it produces:
  markdown  - statement rendered from LeetCode's HTML
  python    - the python3 starter snippet (real signatures)
  method    - required method name for single-call problems
  tests     - pre-parsed example tests:
                call mode: [{"args": [...], "want": ...}, ...]
                ops mode:  [{"ops": [...], "args": [[...], ...], "want": [...]}]
  mode      - "call" | "ops"
  sem       - comparison semantics flags for the runner (see CURATED)

Run:  python3 scripts/build_problems.py
"""
from __future__ import annotations

import ast
import html as html_mod
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from grind.scheduler import bank  # noqa: E402

HERE = Path(__file__).parent
RAW = HERE / "raw_problems.json"
OUT = HERE.parent / "grind" / "problems.json"

# ---------------------------------------------------------------- html -> md

class Md(HTMLParser):
    """LeetCode statement HTML -> markdown. Block tags newline; inline kept."""
    VOID = {"br": "\n", "hr": "---\n"}
    BLOCK = {"p", "pre", "ul", "ol", "li", "h1", "h2", "h3", "h4", "blockquote", "table", "tr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.pre = 0
        self.list_stack = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "pre":
            self.pre += 1
            self.out.append("\n```\n")
        elif tag in ("strong", "b"):
            self.out.append("**")
        elif tag in ("em", "i"):
            self.out.append("*")
        elif tag == "code":
            self.out.append("`" if not self.pre else "")
        elif tag == "li":
            self.out.append("\n- ")
        elif tag in ("ul", "ol"):
            self.list_stack.append(tag)
            self.out.append("\n")
        elif tag in ("p", "h1", "h2", "h3", "h4"):
            self.out.append("\n\n")
        elif tag == "img":
            alt, src = a.get("alt", ""), a.get("src", "")
            self.out.append(f"![{alt}]({src})")
        elif tag == "a":
            self.out.append("[")
        elif tag == "sup":
            self.out.append("^")
        elif tag == "sub":
            self.out.append("~")
        elif tag == "br":
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag == "pre":
            self.pre -= 1
            self.out.append("\n```\n")
        elif tag in ("strong", "b"):
            self.out.append("**")
        elif tag in ("em", "i"):
            self.out.append("*")
        elif tag == "code":
            if not self.pre:
                self.out.append("`")
        elif tag in ("ul", "ol"):
            if self.list_stack:
                self.list_stack.pop()
            self.out.append("\n")
        elif tag in ("p", "h1", "h2", "h3", "h4", "blockquote"):
            self.out.append("\n")
        elif tag == "a":
            self.out.append("]")
        elif tag == "li":
            self.out.append("\n")

    def handle_data(self, data):
        self.out.append(data)

    def result(self):
        text = "".join(self.out)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def to_markdown(html: str) -> str:
    p = Md()
    p.feed(html)
    return p.result()

# ------------------------------------------------------------- example parse

def _pyval(s: str):
    s = s.strip()
    for a, b in (("true", "True"), ("false", "False"), ("null", "None")):
        s = re.sub(rf"\b{a}\b", b, s)
    return ast.literal_eval(s)


def _split_top(s: str) -> list[str]:
    """Split on top-level commas (bracket/quote aware)."""
    parts, depth, q, cur = [], 0, None, []
    for ch in s:
        if q:
            cur.append(ch)
            if ch == q:
                q = None
            continue
        if ch in "\"'":
            q = ch
            cur.append(ch)
        elif ch in "[({":
            depth += 1
            cur.append(ch)
        elif ch in "])}":
            depth -= 1
            cur.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    if "".join(cur).strip():
        parts.append("".join(cur))
    return [p.strip() for p in parts if p.strip()]


def _text_of(html: str) -> str:
    """Statement as plain text: block tags become newlines, inline tags are
    dropped (content kept), entities decoded. Works for both LC layouts —
    <pre> example blocks and the newer <p>-per-line format."""
    t = re.sub(r"</?(p|li|ul|ol|pre|blockquote|h\d|table|tr|td)[^>]*>", "\n", html)
    t = re.sub(r"<br\s*/?>", "\n", t)
    t = re.sub(r"<[^>]+>", "", t)
    t = html_mod.unescape(t).replace("\xa0", " ")
    return t

M_IN = re.compile(r"^input\b:?\s*", re.I)
M_OUT = re.compile(r"^output\b:?\s*", re.I)
M_END = re.compile(r"^(explanation|note|follow[- ]up|example\b|constraints)\b:?", re.I)


def _example_chunks(text: str) -> list[tuple[str, str]]:
    """(input, output) pairs from statement text. Markers appear both as
    "Input:" and bare "Input"; Explanation/Note/Example/Constraints end a
    chunk. Values may span multiple lines (ops sequences, matrices)."""
    pairs, inp, outp, kind = [], [], [], None

    def close():
        if kind == "out" and inp:
            pairs.append(("\n".join(inp), "\n".join(outp)))

    for ln in text.split("\n"):
        s = ln.strip()
        m = M_IN.match(s)
        if m:
            close()                       # an unterminated input has no output — drop it
            inp, outp, kind = [], [], "in"
            rest = s[m.end():]
            if rest:
                inp.append(rest)
            continue
        m = M_OUT.match(s)
        if m:
            kind = "out"
            rest = s[m.end():]
            if rest:
                outp.append(rest)
            continue
        if M_END.match(s):
            close()
            kind = None
        elif kind == "in":
            inp.append(s)
        elif kind == "out":
            outp.append(s)
    close()
    return pairs


def parse_examples(html: str) -> tuple[str, list[dict]]:
    """Returns (mode, tests). mode: 'call' | 'ops'."""
    tests = []
    for inp, outp in _example_chunks(_text_of(html)):
        inp_lines = [l for l in inp.split("\n") if l.strip()]
        outp = outp.strip()
        if not outp:
            continue
        # ops mode: first input line is a list of op names, then arg lists
        if len(inp_lines) >= 2:
            try:
                ops = _pyval(inp_lines[0])
                ok_ops = bool(ops) and all(isinstance(o, str) for o in ops)
            except (ValueError, SyntaxError):
                ok_ops = False
            if ok_ops:
                try:
                    # all argument rows arrive packed in one line: a JSON
                    # array with one entry per op
                    args = _pyval(" ".join(inp_lines[1:]))
                    want = _pyval(outp)
                except (ValueError, SyntaxError):
                    continue
                if isinstance(args, list) and len(args) == len(ops) \
                        and len(want) == len(ops):
                    tests.append({"ops": ops, "args": args, "want": want})
                    continue
        # call mode: "name = value, name = value"
        try:
            want = _pyval(outp)
        except (ValueError, SyntaxError):
            continue
        args = {}
        ok = True
        for part in _split_top(inp.replace("\n", " ")):
            if re.match(r"^[A-Za-z_][A-Za-z_0-9]*\s*=", part):
                name, _, val = part.partition("=")
                try:
                    args[name.strip()] = _pyval(val)
                except (ValueError, SyntaxError):
                    ok = False
                    break
            else:  # bare value, e.g. a single unnamed input
                try:
                    args["__bare__"] = _pyval(part)
                except (ValueError, SyntaxError):
                    ok = False
                    break
        if ok and (args or want is not None):
            tests.append({"args": args, "want": want})
    mode = "ops" if tests and "ops" in tests[0] else "call"
    return mode, tests

# ------------------------------------------------------------ python snippet

def strip_preamble(code: str) -> str:
    """Drop the commented-out (or docstring-wrapped) node-class definitions
    LeetCode prepends to snippets — grind emits its own, real ones."""
    lines = code.split("\n")
    if lines and lines[0].strip().startswith('"""') and "Definition for" in "\n".join(lines[:10]):
        i = 1
        while not lines[i].strip().endswith('"""'):
            i += 1
        return "\n".join(lines[i + 1:]).lstrip("\n")
    j = 0
    while j < len(lines) and lines[j].lstrip().startswith("#"):
        j += 1
    if j and "Definition for" in "\n".join(lines[:j]):
        return "\n".join(lines[j:]).lstrip("\n")
    return code


def normalize(code: str) -> str:
    """Make the starter snippet valid Python: current LeetCode snippets end
    methods with a bare `def ...:` and no body, which would be a SyntaxError.
    Insert `pass` when a method header closes and no deeper line follows
    (skipping blank lines). Class headers are left alone — their defs come
    later in the snippet."""
    lines = code.rstrip().split("\n")
    out = []
    in_def = False          # inside a (possibly multi-line) method header
    for i, ln in enumerate(lines):
        out.append(ln)
        if not ln.strip() or ln.lstrip().startswith("#"):
            continue
        if re.match(r"\s*def\s+\w+\s*\(", ln):
            in_def = True
        if in_def and ln.rstrip().endswith(":"):
            my_ind = len(ln) - len(ln.lstrip())
            nxt_ind = None
            for later in lines[i + 1:]:
                if later.strip():
                    nxt_ind = len(later) - len(later.lstrip())
                    break
            if nxt_ind is None or nxt_ind <= my_ind:
                out.append(" " * (my_ind + 4) + "pass")
            in_def = False
    return "\n".join(out)

def method_of(code: str) -> str | None:
    """Last method name defined in the starter class."""
    names = re.findall(r"^\s*def\s+(\w+)\s*\(", code, re.M)
    return names[-1] if names else None


def params_of(code: str) -> list[str]:
    """Parameter names of the starter method (self excluded). Anchored to
    method_of's method — snippets may define helper classes with __init__."""
    name = method_of(code)
    if not name:
        return []
    m = re.search(rf"^\s*def\s+{name}\s*\(([^)]*)\)", code, re.M)
    if not m:
        return []
    params = [p.split(":")[0].split("=")[0].strip() for p in m.group(1).split(",")]
    return [p for p in params if p and p != "self"]

# ----------------------------------------------------------------- curation
# Comparison semantics the runner can't infer from the examples alone.
# unordered       : outer list compared as a multiset of rows
# unordered_inner : rows themselves compared as multisets
# inplace         : index of the argument mutated in place (want = final state)
# node_out_value  : method returns a tree/list node; want is its value
# custom          : hand-written tests (examples can't express the check)

CURATED: dict[str, dict] = {
    # any-order answers: compared as multisets (rows, and row contents too
    # where LeetCode accepts any permutation within each row)
    "two-sum":                       {"unordered": True},
    "3sum":                          {"unordered": True, "unordered_inner": True},
    "group-anagrams":                {"unordered": True, "unordered_inner": True},
    "subsets":                       {"unordered": True, "unordered_inner": True},
    "subsets-ii":                    {"unordered": True, "unordered_inner": True},
    "permutations":                  {"unordered": True, "unordered_inner": True},
    "combination-sum":               {"unordered": True, "unordered_inner": True},
    "combination-sum-ii":            {"unordered": True, "unordered_inner": True},
    "letter-combinations-of-a-phone-number": {"unordered": True, "unordered_inner": True},
    "palindrome-partitioning":       {"unordered": True, "unordered_inner": True},
    "word-search-ii":                {"unordered": True, "unordered_inner": True},
    "generate-parentheses":          {"unordered": True, "unordered_inner": True},
    "top-k-frequent-elements":       {"unordered": True},
    "k-closest-points-to-origin":    {"unordered": True},
    "course-schedule-ii":            {"unordered": True},
    "pacific-atlantic-water-flow":   {"unordered": True},
    # method mutates an argument in place; want is the final state
    "rotate-image":                  {"inplace": 0},
    "set-matrix-zeroes":             {"inplace": 0},
    "reorder-list":                  {"inplace": 0},
    "surrounded-regions":            {"inplace": 0},
    # float answers accepted within 1e-5
    "powx-n":                        {"float": True},
    "median-of-two-sorted-arrays":   {"float": True},
    "find-median-from-data-stream":  {"float": True},
    # any valid answer — validity is checked, not equality
    "n-queens":                      {"nqueens": True},
    "longest-palindromic-substring": {"palindromic_substring": True},
    # node identity quirks
    "lowest-common-ancestor-of-a-binary-search-tree": {"node_out_value": True},
    "clone-graph":                   {"graph": True, "alias": {"node": "adjList"}},
}

# Round-trip checks the examples can't express: the published example is
# "serialize this tree, get it back" — encoded as ops with "@prev" chaining.
TEST_OVERRIDES: dict[str, dict] = {
    "serialize-and-deserialize-binary-tree": {
        "mode": "ops",
        "tests": [
            {"ops": ["Codec", "serialize", "deserialize"],
             "args": [[], [[1, 2, 3, None, None, 4, 5]], ["@prev"]],
             "want": [None, None, [1, 2, 3, None, None, 4, 5]]},
            {"ops": ["Codec", "serialize", "deserialize"],
             "args": [[], [[]], ["@prev"]],
             "want": [None, None, []]},
        ],
    },
}


def main() -> None:
    raw = json.loads(RAW.read_text())
    out, problems = {}, []
    premium = json.loads((HERE / "premium.json").read_text())
    for p in bank():
        slug = p["slug"]
        q = raw.get(slug)
        if not q:
            problems.append((slug, "MISSING RAW"))
            continue
        html = q.get("content") or ""
        py = next((c["code"] for c in (q.get("codeSnippets") or [])
                   if c["langSlug"] == "python3"), None)
        if not html or not py:                      # premium problems: hand-bundled
            ov = premium.get(slug)
            if ov:
                entry = {"markdown": ov["markdown"], "python": ov["python"].rstrip(),
                          "method": ov.get("method") or method_of(ov["python"]),
                          "mode": ov["mode"], "tests": ov["tests"], "sem": ov.get("sem", {})}
                out[slug] = entry
                problems.append((slug, f"ok {ov['mode']} x{len(ov['tests'])} (bundled)"))
            else:
                problems.append((slug, "NO CONTENT/SNIPPET"))
            continue
        mode, tests = parse_examples(html)
        ov_tests = TEST_OVERRIDES.get(slug)
        if ov_tests:
            mode, tests = ov_tests["mode"], ov_tests["tests"]
        params = params_of(py)
        alias = CURATED.get(slug, {}).get("alias", {})
        if mode == "call":
            fixed = []
            for t in tests:
                if "__bare__" in t["args"] and len(params) == 1:
                    t["args"] = [t["args"]["__bare__"]]
                try:
                    t["args"] = [t["args"][alias.get(nm, nm)] for nm in params]
                except KeyError as e:
                    problems.append((slug, f"ARG MISMATCH {e}"))
                    fixed = []
                    break
                fixed.append(t)
            tests = fixed
        if not tests:
            problems.append((slug, "NO TESTS PARSED"))
            continue
        entry = {"markdown": to_markdown(html), "python": normalize(strip_preamble(py)),
                 "method": method_of(py), "mode": mode, "tests": tests,
                 "sem": CURATED.get(slug, {})}
        out[slug] = entry
        problems.append((slug, f"ok {mode} x{len(tests)}"
                        + (" SEM:" + ",".join(entry["sem"]) if entry["sem"] else "")))
    OUT.write_text(json.dumps(out, indent=1))
    bad = [(s, w) for s, w in problems if not w.startswith("ok")]
    for s, w in problems:
        print(f"{w:24} {s}")
    print(f"\n{len(out)}/150 built; failures: {len(bad)}")
    if bad:
        print("\n".join(f"  {s}: {w}" for s, w in bad))


if __name__ == "__main__":
    main()
