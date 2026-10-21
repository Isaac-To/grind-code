#!/usr/bin/env python3
"""Bank-wide gate: every problem's bundled tests + hand-written edge cases
must pass its reference solution (scripts/references/<slug>.py) through the
REAL runner. Run after scripts/build_problems.py; exit 1 on any failure.

This is the check that keeps the edge-case bank honest — an unverified
expected value would corrupt `grind done` grading, so nothing ships unless
every reference passes everything here.
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

HERE = Path(__file__).parent


def _load(path: Path):
    mod = types.ModuleType(f"ref_{path.stem.replace('-', '_')}")
    mod.__file__ = str(path)
    exec(compile(path.read_text(), str(path), "exec"), mod.__dict__)
    return mod


def main() -> int:
    failures = []
    checked = extras_n = 0
    for f in sorted((HERE / "extras").glob("*.json")):
        for slug, cases in json.loads(f.read_text()).items():
            entry = problems.get(slug)
            ref = HERE / "references" / f"{slug}.py"
            if not entry or not ref.exists():
                failures.append((slug, "missing entry or reference"))
                continue
            # bundled + extras in runner shape (call-mode dicts -> tuples)
            def shape(t):
                if isinstance(t, dict) and "ops" not in t:
                    return (tuple(t["args"]), t["want"])
                return t
            tests = [shape(t) for t in entry["tests"] + cases]
            buf = io.StringIO()
            try:
                with redirect_stdout(buf):
                    passed, total = problems.run_tests(_load(ref), tests, slug)
            except Exception as e:
                failures.append((slug, f"{type(e).__name__}: {e}"))
                continue
            checked += 1
            extras_n += len(cases)
            if passed != total:
                print(buf.getvalue())
                failures.append((slug, f"{passed}/{total}"))
    print(f"verified {checked} problems, {extras_n} edge cases; failures: {len(failures)}")
    for slug, why in failures:
        print(f"  FAIL {slug}: {why}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
