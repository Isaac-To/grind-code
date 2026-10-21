#!/usr/bin/env python3
"""Authoring gate for hand-written edge-case tests (scripts/extras/*.json).

An edge case enters the bank only through a verified reference solution
(scripts/references/<slug>.py): the reference must pass the problem's
bundled examples through the REAL runner, and every extra's `want` is
computed by grind.problems.evaluate — the exact conversion semantics
`grind done` grades with. A reference that fails its examples is wrong;
fix the reference, never the examples.

usage:
  edge_tool.py verify <slug> <reference.py> [extras.json]   all must pass
  edge_tool.py want <slug> <reference.py> <case.json>       print computed want

extras/case files hold test entries in the bank's own shapes:
  call mode: {"args": [...]}                    (want filled by the tool)
  ops mode:  {"ops": [...], "args": [...]}       (want list filled per op)
extras.json may be a list of entries or {"<slug>": [entries, ...]}.
"""
from __future__ import annotations

import io
import json
import sys
import types
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from grind import problems  # noqa: E402


def _runner_shaped(tests: list) -> list:
    """Bundled/extras call-mode entries are {"args", "want"} dicts; the
    runner wants the scaffold's tuple form ((args...), want). Ops dicts,
    already the runner's shape, pass through untouched."""
    return [t if not isinstance(t, dict) or "ops" in t else (tuple(t["args"]), t["want"])
            for t in tests]

def _load(path: Path):
    """Compile-and-exec, like grind's own solution loader (no pycache)."""
    mod = types.ModuleType(f"ref_{path.stem.replace('-', '_')}")
    mod.__file__ = str(path)
    exec(compile(path.read_text(), str(path), "exec"), mod.__dict__)
    return mod


def _entries(raw: dict | list, slug: str) -> list:
    if isinstance(raw, dict):
        if slug in raw:
            return raw[slug]
        if "args" in raw or "ops" in raw:
            return [raw]
        sys.exit(f"extras file has no entry for {slug}")
    return raw


def _verify(slug: str, ref_path: Path, extras_path: Path | None) -> int:
    entry = problems.get(slug)
    if not entry:
        sys.exit(f"unknown slug: {slug}")
    tests = list(entry["tests"])
    if extras_path:
        tests += _entries(json.loads(extras_path.read_text()), slug)
    buf = io.StringIO()
    with redirect_stdout(buf):
        passed, total = problems.run_tests(_load(ref_path), _runner_shaped(tests), slug)
    print(buf.getvalue().rstrip())
    print(f"{slug}: {passed}/{total} passed" + ("" if passed == total else "  — REFERENCE OR CASE IS WRONG"))
    return 0 if passed == total else 1


def _want(slug: str, ref_path: Path, case_path: Path) -> int:
    case = json.loads(case_path.read_text())
    got = problems.evaluate(_load(ref_path), case, slug)
    print(json.dumps(got))
    return 0


def main() -> int:
    if len(sys.argv) < 4 or sys.argv[1] not in ("verify", "want"):
        print(__doc__)
        return 2
    cmd, slug, ref = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    if cmd == "verify":
        return _verify(slug, ref, Path(sys.argv[4]) if len(sys.argv) > 4 else None)
    return _want(slug, ref, Path(sys.argv[4]))


if __name__ == "__main__":
    raise SystemExit(main())
