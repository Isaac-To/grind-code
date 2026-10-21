#!/usr/bin/env python3
"""One-time fetcher: pull every bank problem's statement + code snippets from
LeetCode's public GraphQL endpoint into scripts/raw_problems.json.

Stdlib-only, resumable (skips slugs already fetched), polite pacing.
Run:  python3 scripts/fetch_problems.py
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from grind.scheduler import bank  # noqa: E402

RAW = Path(__file__).parent / "raw_problems.json"
URL = "https://leetcode.com/graphql"
QUERY = """
query($slug: String!) {
  question(titleSlug: $slug) {
    questionFrontendId
    title
    difficulty
    content
    codeSnippets { lang langSlug code }
  }
}
"""
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"),
    "Referer": "https://leetcode.com/problemset/",
}


def fetch(slug: str) -> dict | None:
    body = json.dumps({"query": QUERY, "variables": {"slug": slug}}).encode()
    req = urllib.request.Request(URL, data=body, headers=HEADERS, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())
    q = data.get("data", {}).get("question")
    if not q:
        print(f"  {slug}: MISSING ({data.get('errors')})")
        return None
    return q


def main() -> None:
    raw = json.loads(RAW.read_text()) if RAW.exists() else {}
    slugs = [p["slug"] for p in bank()]
    todo = [s for s in slugs if s not in raw]
    print(f"{len(slugs)} bank problems, {len(slugs) - len(todo)} already fetched")
    for i, slug in enumerate(todo, 1):
        for attempt in (1, 2, 3):
            try:
                q = fetch(slug)
                if q:
                    raw[slug] = q
                    print(f"  [{i}/{len(todo)}] {slug}: ok")
                    break
            except Exception as e:
                print(f"  [{i}/{len(todo)}] {slug}: attempt {attempt} failed ({e})")
                time.sleep(5 * attempt)
        else:
            print(f"  {slug}: GIVING UP")
        if i % 10 == 0:
            RAW.write_text(json.dumps(raw))
            print("  (saved)")
        time.sleep(0.8)
    RAW.write_text(json.dumps(raw))
    missing = [s for s in slugs if s not in raw]
    print(f"done: {len(raw)}/{len(slugs)} fetched" + (f", MISSING: {missing}" if missing else ""))


if __name__ == "__main__":
    main()
