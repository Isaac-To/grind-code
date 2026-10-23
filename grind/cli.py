"""grind — FSRS-driven LeetCode fluency trainer.

Loop:  grind next   -> presents the best problem, writes a scaffold, starts timer
       grind done   -> stop timer, grade from time+outcome, FSRS schedules the next rep
"""
from __future__ import annotations

import argparse
import io
import json
import os
import shutil
import subprocess
import sys
import types
import webbrowser
from contextlib import redirect_stdout
from datetime import datetime, timedelta
from pathlib import Path

from . import update
from . import __version__
from . import scheduler as sch
from . import problems
from . import store
READY_GOAL = 0.80  # overall readiness at which you're interview ready
INTRO = """
Welcome to grind — a spaced-repetition trainer for the NeetCode 150 (the OA pattern set).
The daily loop:
  grind next    presents the best problem — due reviews first, otherwise a new
                one from your least-ready topic; its environment appears in
                ./solutions/ (statement, real signature, pre-filled tests)
  grind check   quick test of your solution against a few cases (while you solve)
  grind done    runs the FULL test suite, grades you on outcome + time, and
                schedules the next review automatically
Everything else is automatic: what to practice, when to review, and how interview-ready
you are (grind status / topics / stats show the numbers). State lives in ~/.grind-code,
and every session is backed up automatically — you'll pick where in a moment.
grind also checks GitHub once a day for a newer version and tells you how to
get it (grind update). Nothing is ever installed without your say-so, and
grind config update_check=false turns the check off.
"""
DIFF_COLOR = {"Easy": "\033[32m", "Medium": "\033[33m", "Hard": "\033[31m"}
RESET = "\033[0m"
BOLD = "\033[1m"


def url(slug: str) -> str:
    return f"https://leetcode.com/problems/{slug}/"


def _fmt_min(m: float) -> str:
    m = round(m)
    return f"{m // 60}h{m % 60:02d}m" if m >= 60 else f"{m}m"


# ---------------------------------------------------------------- session

def _legacy_scaffold(prob: dict, target: float, phase: str) -> str:
    """Scaffold for problems with no bundled environment data."""
    return (
        f'"""\n{prob["num"]}. {prob["title"]}  [{prob["difficulty"]}]  ({prob["topic"]})\n\n'
        f"{url(prob['slug'])}\n"
        f'Fluency target: {target} min ({phase})\n"""\n'
        "\nclass Solution:\n"
        "    def solve(self):\n"
        "        pass\n"
        "\n# quick check: grind check   -- fill from the problem's examples\n"
        "# single-method solutions are auto-discovered; the last public method\n"
        "# wins if you define helpers.\n"
        "TESTS = [\n"
        "    # ((args...), expected),\n"
        "]\n"
    )


def _archive_solution(sol_dir: Path, slug: str, scaffold: Path) -> Path:
    """Move a finished rep's solution out of the way — full history stays on
    disk (and in every backup): solutions/archive/<slug>/attempt-N.py."""
    arch = sol_dir / "archive" / slug
    arch.mkdir(parents=True, exist_ok=True)
    n = 1 + sum(1 for _ in arch.glob("attempt-*.py"))
    dest = arch / f"attempt-{n}.py"
    shutil.move(str(scaffold), str(dest))
    return dest


def _archive_statement(sol_dir: Path, slug: str) -> None:
    """File the statement away with the problem's history — solutions/ shows
    only the active problem. It is re-rendered from the bundle whenever the
    problem returns, so this is pure tidying."""
    md = sol_dir / f"{slug}.md"
    if md.exists():
        dest = sol_dir / "archive" / slug / "statement.md"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(md), str(dest))


def _file_wip(sol_dir: Path, slug: str, scaffold: Path) -> Path:
    """Park an ungraded attempt as archive/<slug>/wip.py — the latest skip
    wins; it is restored the next time the problem is picked."""
    dest = sol_dir / "archive" / slug / "wip.py"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(scaffold), str(dest))
    return dest


def _tidy_solutions(sol_dir: Path, keep: str, state: dict) -> None:
    """solutions/ holds only the active problem's environment. Files of other
    known problems — pre-grind solutions, strays, restore leftovers — are
    filed into their archive/ here: a passing file is a finished solution
    (attempt-N), anything else is resumable WIP (wip.py), statements go to
    statement.md. Unknown files are never touched."""
    bank = sch.by_slug()
    for p in sorted(sol_dir.iterdir()):
        if not p.is_file() or p.stem == keep or p.suffix not in (".py", ".md"):
            continue
        slug = p.stem
        if slug not in bank:
            continue
        if p.suffix == ".md":
            _archive_statement(sol_dir, slug)
        elif _file_passes_tests(p, slug):
            _archive_solution(sol_dir, slug, p)
        else:
            _file_wip(sol_dir, slug, p)
        state["graded_files"].pop(slug, None)  # its attempt is filed; flag's job is done


def _file_passes_tests(scaffold: Path, slug: str) -> bool:
    """The file on disk is a complete working solution: it loads and passes
    its own full TESTS suite. Blank scaffolds, WIP, and files without tests
    fail this check and are never touched."""
    try:
        mod = _load_solution(scaffold)
        tests = getattr(mod, "TESTS", None)
        if not tests:
            return False
        with redirect_stdout(io.StringIO()):
            passed, total = problems.run_tests(mod, tests, slug)
        return total > 0 and passed == total
    except Exception:
        return False


def start_session(state: dict, prob: dict, why: str) -> None:
    now = sch.utcnow()
    sol_dir = Path(os.environ.get("GRIND_SOLUTIONS", "solutions"))
    sol_dir.mkdir(parents=True, exist_ok=True)
    scaffold = sol_dir / f"{prob['slug']}.py"
    target, phase = sch.target_info(state, prob)
    entry = problems.get(prob["slug"])
    _tidy_solutions(sol_dir, prob["slug"], state)
    wip = sol_dir / "archive" / prob["slug"] / "wip.py"
    if not scaffold.exists() and wip.exists():
        # An ungraded attempt was parked here earlier — resume, not restart.
        shutil.move(str(wip), str(scaffold))
    archived = None
    if scaffold.exists():
        if why == "review" and state["graded_files"].pop(prob["slug"], None):
            # Legacy migration: older grind versions left the graded file in
            # place with this flag, archiving it only on resurface. Consume
            # the flag, keep the old attempt in archive/, start from a blank
            # scaffold. Ungraded work (a skip, mid-solve edits) has no flag
            # and is never touched.
            archived = _archive_solution(sol_dir, prob["slug"], scaffold)
        elif _file_passes_tests(scaffold, prob["slug"]):
            # A working solution is already on disk — a file from before grind,
            # or an attempt finished but never graded. Its own TESTS are the
            # judge: passing means archived + blank scaffold (prove you can
            # still produce it); anything blank, half-done, or without tests
            # stays exactly where it is.
            archived = _archive_solution(sol_dir, prob["slug"], scaffold)
    if not scaffold.exists():
        scaffold.write_text(problems.render_py(prob, entry, target, phase) if entry
                            else _legacy_scaffold(prob, target, phase))
    md = sol_dir / f"{prob['slug']}.md"
    if entry and not md.exists():
        md.write_text(problems.render_md(prob, entry, target, phase))
    state["session"] = {"slug": prob["slug"], "started": now.isoformat(), "why": why,
                        "scaffold": str(scaffold)}
    store.save(state)

    print(f"{BOLD}{prob['num']}. {prob['title']}{RESET}  "
          f"{DIFF_COLOR[prob['difficulty']]}{prob['difficulty']}{RESET}  ·  {prob['topic']}  ·  {why}")
    print(f"  {url(prob['slug'])}")
    env = f"statement: {md}" if entry else ""
    print(f"  scaffold: {scaffold}   (target {_fmt_min(target)} · {phase})" +
          (f"   ·   {env}" if env else ""))
    if archived:
        print(f"  prior attempt → {archived}   ·   fresh scaffold — solve from memory")
    print("  solve it in your IDE, verify with `grind check`, then grade with `grind done`")


def cmd_next(args) -> None:
    state = store.load()
    if state["session"]:
        sess = state["session"]
        p = sch.by_slug()[sess["slug"]]
        if "paused_at" in sess:
            # Session is paused — resume it
            paused_at = datetime.fromisoformat(sess["paused_at"])
            paused_dur = (sch.utcnow() - paused_at).total_seconds()
            sess["paused_total"] = sess.get("paused_total", 0.0) + paused_dur
            paused_fmt = _fmt_min(sess["paused_total"] / 60)
            del sess["paused_at"]
            store.save(state)
            print(f"Resumed: {p['title']}  (paused {paused_fmt})")
        else:
            el = (sch.utcnow() - datetime.fromisoformat(sess["started"])).total_seconds() / 60
            print(f"Session already active: {p['title']}  ({_fmt_min(el)} elapsed)")
            print("Finish it first:  grind done  /  grind skip  /  grind pause")
        return
    if not state.get("seen_intro"):
        print(INTRO)
        state["seen_intro"] = True
        ans = _ask_repo()
        if ans:
            repo_url = _save_remote(state, ans)
            if repo_url and _restore_if_grind_repo(repo_url):
                state = store.load()              # adopt restored progress
                state["seen_intro"] = True
                _save_remote(state, ans)          # keep this machine's repo answer
                store.save(state)
                print("  restored your grind progress — you're back where you left off")
        store.save(state)
    now = sch.utcnow()
    prob, why = sch.pick_next(state, now, ahead=args.ahead, new=args.new)
    if prob is None:
        if args.ahead:
            print("No upcoming reviews to pull.")
        elif args.new:
            print("No new problems available.")
        else:
            print("All caught up — nothing due right now.")
            nxt = sorted((datetime.fromisoformat(d["due"]), s) for s, d in state["cards"].items())
            if nxt:
                print(f"Next review: {sch.by_slug()[nxt[0][1]]['title']} in {sch.fmt_interval(nxt[0][0], now)}")
        return
    start_session(state, prob, "review" if why == "review" else "new problem")
    if args.web or state["config"].get("auto_web"):
        webbrowser.open(url(prob["slug"]))
    if args.edit or state["config"].get("auto_edit"):
        subprocess.call([os.environ.get("EDITOR", "vi"), state["session"]["scaffold"]])

def cmd_pause(args) -> None:
    """Pause the active session timer."""
    state = store.load()
    sess = state["session"]
    if not sess:
        sys.exit("No active session. Start one with: grind next")
    if "paused_at" in sess:
        sys.exit("Session already paused. Resume with: grind next")
    sess["paused_at"] = sch.utcnow().isoformat()
    store.save(state)
    prob = sch.by_slug()[sess["slug"]]
    print(f"Paused: {prob['title']}. Resume with: grind next")


def cmd_help(args) -> None:
    """Print a friendly command overview grouped by purpose."""
    print("grind — FSRS-driven LeetCode fluency trainer")
    print()
    print("Daily loop:")
    print("  grind next      present the best problem, write scaffold, start timer")
    print("  grind pause     pause the active session timer")
    print("  grind check     quick test (first 3 cases) while you solve")
    print("  grind done      run full suite, grade on outcome + time, schedule rep")
    print("  grind skip      drop session without grading (work kept in archive/)")
    print()
    print("Inspect & learn:")
    print("  grind status    one-line progress snapshot (readiness, streak, due)")
    print("  grind topics    per-topic readiness breakdown")
    print("  grind stats     streaks, solved counts, trends, activity")
    print("  grind reference print the verified reference solution for a problem")
    print("  grind extras    print the hand-written edge cases for a problem")
    print()
    print("Config & maintenance:")
    print("  grind config    show or set config (e.g. daily_new=3)")
    print("  grind backup    back up now (auto after every grind done)")
    print("  grind restore   pull backup onto a new machine")
    print("  grind update    pull latest version and reinstall")
    print()
    print("Run `grind <command> --help` for options on any command.")
    print("Run `grind` with no args → same as `grind next`.")
def cmd_done(args) -> None:
    state = store.load()
    sess = state["session"]
    if not sess:
        sys.exit("No active session. Start one with: grind next")
    prob = sch.by_slug()[sess["slug"]]
    now = sch.utcnow()
    paused_total = sess.get("paused_total", 0.0)
    if "paused_at" in sess:
        # Currently paused — add current pause to total
        paused_at = datetime.fromisoformat(sess["paused_at"])
        paused_total += (now - paused_at).total_seconds()
    elapsed = args.mins if args.mins is not None else \
        max(0.0, (now - datetime.fromisoformat(sess["started"])).total_seconds() / 60 - paused_total / 60)
    if args.rating is not None and not 1.0 <= args.rating <= 4.0:
        sys.exit("rating override must be within 1..4")

    # Full-suite gate: when TESTS exist they are ground truth for "solved";
    # the solved prompt/flags are the fallback when no tests are defined.
    sol_path = Path(os.environ.get("GRIND_SOLUTIONS", "solutions")) / f"{sess['slug']}.py"
    passed = total = None
    solved = None
    if sol_path.exists():
        try:
            mod = _load_solution(sol_path)
            tests = getattr(mod, "TESTS", None)
        except Exception as e:
            print(f"  solution file fails to load ({type(e).__name__}: {e})")
            solved = False
        if solved is None and tests:
            try:
                passed, total = problems.run_tests(mod, tests, sess["slug"])
            except ValueError as e:
                print(f"  {e}")
                solved = False
            if solved is None:
                print(f"  full suite: {passed}/{total} passed")
                solved = passed == total
    if solved is None:
        solved = args.solved if args.solved is not None else _ask_solved(prob, elapsed)
    elif total and args.solved is not None and args.solved != solved:
        print("  note: --solved/--fail overridden by TESTS (tests are authoritative)")

    target, phase = sch.target_info(state, prob)
    rating_f = args.rating if args.rating is not None else sch.rating_float(solved, elapsed, target)

    card, was_new = sch.apply_review(state, sess["slug"], rating_f, now)
    state["logs"].append({"slug": sess["slug"], "rating": round(rating_f, 2), "solved": solved,
                          "elapsed": round(elapsed, 1), "new": was_new, "ts": now.isoformat(),
                          "tests": f"{passed}/{total}" if total else None})
    archived = None
    if sol_path.exists():
        # A graded rep is history the moment it's graded: file it under
        # archive/ and leave solutions/ to work in progress only. The
        # graded_files flag is no longer set here — but legacy state may still
        # carry one from the old deferred behavior; start_session consumes it.
        archived = _archive_solution(sol_path.parent, sess["slug"], sol_path)
    _archive_statement(sol_path.parent, sess["slug"])   # only the active problem stays visible
    state["session"] = None
    state["last"] = sess["slug"]
    store.save(state)

    f_score = sch.fluency_score(solved, elapsed / target)
    print(f"{prob['title']}: {'solved' if solved else 'unsolved'} in {_fmt_min(elapsed)} "
          f"(target {_fmt_min(target)} · {phase})  ·  rating {rating_f:.2f}/4")
    if phase != "locked" and sch.target_info(state, prob)[1] == "locked":
        print("  target locked at your demonstrated pace — sustaining it now earns steady good ratings.")
    print(f"  next review in {sch.fmt_interval(card.due, now)}")
    if not solved:
        if total and passed < total:
            print("  failing tests — counted as unsolved; fix it and grind next brings it right back.")
        else:
            print("  look at the solution, understand it fully, then move on — it will resurface soon.")
    elif f_score < 0.55:
        print("  solved, but a struggle — FSRS will keep this one close until it's smooth.")
    print(f"  new today: {min(sch.new_today(state, now), state['config']['daily_new'])}/{state['config']['daily_new']}   "
          f"due now: {len(sch.due_reviews(state, now))}")
    if archived:
        print(f"  attempt archived → {archived}")
    res = _do_backup(state)
    store.save(state)  # persist backup flags mutated during the silent backup
    if res["error"]:
        print(f"  backup: {res['error']}")


def cmd_edit(args) -> None:
    """Open the active session's scaffold in $EDITOR."""
    state = store.load()
    sess = state["session"]
    if not sess:
        sys.exit("No active session. Start one with: grind next")
    scaffold = Path(sess["scaffold"])
    if not scaffold.exists():
        sys.exit(f"scaffold not found: {scaffold}")
    editor = os.environ.get("EDITOR", "vi")
    subprocess.call([editor, str(scaffold)])


def cmd_web(args) -> None:
    """Open the active session's LeetCode page in the browser."""
    state = store.load()
    sess = state["session"]
    if not sess:
        sys.exit("No active session. Start one with: grind next")
    webbrowser.open(url(sess["slug"]))


def cmd_log(args) -> None:
    """Show recent graded attempts."""
    state = store.load()
    logs = state.get("logs", [])
    if not logs:
        print("No graded attempts yet.")
        return
    limit = len(logs) if args.all else (args.n or 20)
    for entry in reversed(logs[-limit:]):
        ts = datetime.fromisoformat(entry["ts"]).strftime("%Y-%m-%d %H:%M")
        slug = entry["slug"]
        rating = entry.get("rating", 0.0)
        solved = "yes" if entry.get("solved") else "no"
        elapsed = entry.get("elapsed", 0.0)
        tests = entry.get("tests")
        test_str = f"  tests={tests}" if tests else ""
        print(f"{ts}  {slug}  rating={rating:.2f}  elapsed={elapsed:.1f}m  solved={solved}{test_str}")


def cmd_list(args) -> None:
    """List all problems with status (new/due/seen/proven)."""
    state = store.load()
    now = sch.utcnow()
    bank = sch.bank()
    by_slug = {p["slug"]: p for p in bank}
    due_set = set(sch.due_reviews(state, now))
    cards = state.get("cards", {})

    # compute last solved status per slug
    last_solved: dict[str, bool] = {}
    for entry in state.get("logs", []):
        last_solved[entry["slug"]] = entry.get("solved", False)

    rows = []
    for p in bank:
        slug = p["slug"]
        card = cards.get(slug)
        if slug not in cards:
            status = "new"
        elif slug in due_set:
            status = "due"
        elif last_solved.get(slug):
            status = "proven"
        else:
            status = "seen"

        ready = sch.readiness(state, slug, now)
        due_in = ""
        if card:
            c = sch.Card.from_dict(card)
            if c.due > now:
                due_in = sch.fmt_interval(c.due, now)
            else:
                due_in = "now"

        rows.append((slug, p["topic"], p["difficulty"], status, ready, due_in))

    # filters
    if args.topic:
        rows = [r for r in rows if args.topic.lower() in r[1].lower()]
    if args.due:
        rows = [r for r in rows if r[3] == "due"]
    if args.new:
        rows = [r for r in rows if r[3] == "new"]
    if args.proven:
        rows = [r for r in rows if r[3] == "proven"]
    if args.difficulty:
        rows = [r for r in rows if r[2] == args.difficulty]

    # sort: due first (most overdue), then by readiness ascending
    def sort_key(r):
        status_order = {"due": 0, "new": 1, "seen": 2, "proven": 3}
        return (status_order.get(r[3], 4), r[4])
    rows.sort(key=sort_key)

    # print table
    print(f"{'slug':<30} {'topic':<28} {'diff':<6} {'status':<7} {'ready':>6}  due_in")
    for slug, topic, diff, status, ready, due_in in rows:
        print(f"{slug:<30} {topic:<28} {diff:<6} {status:<7} {ready*100:>5.0f}%  {due_in}")

def cmd_upcoming(args) -> None:
    """Show reviews due in the next N days."""
    state = store.load()
    now = sch.utcnow()
    days = args.days or 14
    upcoming = sch.upcoming_reviews(state, now, days)
    if not upcoming:
        print(f"No reviews due in the next {days} days.")
        return
    by_slug = {p["slug"]: p for p in sch.bank()}
    print(f"{'due':<12} {'slug':<30} {'topic':<28} {'diff':<6}")
    for due_dt, slug in upcoming:
        p = by_slug.get(slug)
        if not p:
            continue
        due_str = due_dt.astimezone().strftime("%m-%d %H:%M") if due_dt <= now else due_dt.astimezone().strftime("%m-%d")
        if due_dt <= now:
            due_str += " (overdue)"
        print(f"{due_str:<12} {slug:<30} {p['topic']:<28} {p['difficulty']:<6}")


def _ask_solved(prob: dict, elapsed: float) -> bool:
    print(f"{prob['title']} — {_fmt_min(elapsed)} elapsed.")
    try:
        while True:
            a = input("Solved it? [y/n] ").strip().lower()
            if a in ("y", "n"):
                return a == "y"
    except (EOFError, KeyboardInterrupt):
        sys.exit("no answer — session kept, retry with: grind done")


def cmd_skip(args) -> None:
    state = store.load()
    sess = state["session"]
    if not sess:
        sys.exit("No active session.")
    sol_dir = Path(os.environ.get("GRIND_SOLUTIONS", "solutions"))
    scaffold = sol_dir / f"{sess['slug']}.py"
    if scaffold.exists():
        # Not graded — the work is kept and resumed when the problem returns.
        dest = _file_wip(sol_dir, sess["slug"], scaffold)
        state["graded_files"].pop(sess["slug"], None)
        print(f"  work in progress filed → {dest}")
    _archive_statement(sol_dir, sess["slug"])
    state["session"] = None
    store.save(state)
    print("Session dropped (not graded, not counted).")


def _load_solution(path: Path):
    """Compile the file directly — no __pycache__ consultation, so a same-size
    edit saved in the same second can never serve a stale solution."""
    name = f"grind_check_{path.stem.replace('-', '_')}"
    mod = types.ModuleType(name)
    mod.__file__ = str(path)
    exec(compile(path.read_text(), str(path), "exec"), mod.__dict__)
    return mod



def cmd_check(args) -> None:
    state = store.load()
    slug = args.slug or (state["session"] or {}).get("slug") or state.get("last")
    if not slug:
        sys.exit("pass a problem id (e.g. `two-sum`), run during an active session, or grade something first")
    path = Path(os.environ.get("GRIND_SOLUTIONS", "solutions")) / f"{slug}.py"
    if not path.exists():
        sys.exit(f"no solution file: {path}")
    try:
        mod = _load_solution(path)
        tests = getattr(mod, "TESTS", None)
    except Exception as e:
        sys.exit(f"error loading {path}: {type(e).__name__}: {e}")
    if problems._solution_class(mod) is None:
        sys.exit(f"define your solution class in {path}")
    if not tests:
        sys.exit(f"add TESTS = [((args...), expected), ...] to {path}")
    if not args.all:  # check is a quick subset; grind done runs the full set
        tests = tests[:args.n or 3]
    print(f"checking {slug} ({len(tests)} of {len(getattr(mod, 'TESTS'))} case(s))")
    passed, total = problems.run_tests(mod, tests, slug)
    print(f"{passed}/{total} passed" + ("" if passed == total else " — fix and re-run"))
    if passed < total:
        sys.exit(1)


def cmd_review(args) -> None:
    """Run the full test suite for a problem without grading (no FSRS impact)."""
    state = store.load()
    slug = args.slug or (state["session"] or {}).get("slug") or state.get("last")
    if not slug:
        sys.exit("pass a problem id (e.g. `two-sum`), run during an active session, or grade something first")
    path = Path(os.environ.get("GRIND_SOLUTIONS", "solutions")) / f"{slug}.py"
    if not path.exists():
        sys.exit(f"no solution file: {path}")
    try:
        mod = _load_solution(path)
        tests = getattr(mod, "TESTS", None)
    except Exception as e:
        sys.exit(f"error loading {path}: {type(e).__name__}: {e}")
    if problems._solution_class(mod) is None:
        sys.exit(f"define your solution class in {path}")
    if not tests:
        sys.exit(f"add TESTS = [((args...), expected), ...] to {path}")
    print(f"reviewing {slug} ({len(tests)} case(s))")
    passed, total = problems.run_tests(mod, tests, slug)
    print(f"{passed}/{total} passed" + ("" if passed == total else " — fix and re-run"))
    if passed < total:
        sys.exit(1)


def _scripts_root() -> Path:
    """scripts/ lives next to grind/ at the repo root — cwd-independent."""
    return Path(__file__).resolve().parent.parent / "scripts"


def _slug_from_session(args) -> str:
    slug = args.slug or (store.load()["session"] or {}).get("slug")
    if not slug:
        sys.exit("no slug given — pass one: `grind reference <slug>`")
    return slug


def cmd_reference(args) -> None:
    """Print this problem's verified reference solution — how each edge
    case's expected value was computed (and verified against the runner)."""
    slug = _slug_from_session(args)
    path = _scripts_root() / "references" / f"{slug}.py"
    if not path.exists():
        sys.exit(f"no reference solution for {slug} — confirm the slug, "
                 f"or add one to scripts/references/{slug}.py")
    print(f"Reference solution for {slug} — computed from, and verified against, "
          f"scripts/verify_extras.py")
    print(path.read_text())


def cmd_extras(args) -> None:
    """Edge cases are hidden (like LeetCode's hidden tests). They run silently
    during `grind done`; `grind check` only runs the first few bundled examples.
    """
    slug = _slug_from_session(args)
    path = _scripts_root() / "extras" / f"{slug}.json"
    if not path.exists():
        print(f"no edge cases for {slug} — only the bundled examples exist")
        return
    cases = json.loads(path.read_text()).get(slug)
    if not cases:
        print(f"no edge cases for {slug} — only the bundled examples exist")
        return
    print(f"Edge cases for {slug}: {len(cases)} hidden cases (run with `grind done`)")
    print("These are not shown — like LeetCode's hidden test cases.")

# ---------------------------------------------------------------- views

def cmd_status(args) -> None:
    state = store.load()
    now = sch.utcnow()
    due = len(sch.due_reviews(state, now))
    ready = sch.overall_readiness(state, now)
    cur, best = sch.streaks(state)
    _, _, proven = sch.solved_counts(state)
    print(f"{BOLD}grind status{RESET}  ·  {len(state['cards'])}/150 seen  ·  {due} due  ·  "
          f"{min(sch.new_today(state, now), state['config']['daily_new'])}/{state['config']['daily_new']} new today  ·  "
          f"streak {cur}d (best {best}d)  ·  proven {proven}/150")
    check = " \u2713" if ready >= READY_GOAL else ""
    print(f"interview readiness: {ready*100:.0f}%  (goal {READY_GOAL*100:.0f}%){check}")
    weak = sorted(sch.readiness_by_topic(state, now).items(), key=lambda kv: kv[1])[:3]
    print("least ready: " + "  ".join(f"{t} {v*100:.0f}%" for t, v in weak))
    if state["session"]:
        p = sch.by_slug()[state["session"]["slug"]]
        el = (now - datetime.fromisoformat(state["session"]["started"])).total_seconds() / 60
        print(f"in session: {p['title']} ({_fmt_min(el)} elapsed)")


def cmd_topics(args) -> None:
    state = store.load()
    now = sch.utcnow()
    ready = sch.readiness_by_topic(state, now)
    seen = sch.seen_counts_by_topic(state)
    total = {p["topic"]: 0 for p in sch.bank()}
    for p in sch.bank():
        total[p["topic"]] += 1
    print(f"{'topic':<28} {'seen':>7} {'ready':>8}")
    for t, m in sorted(ready.items(), key=lambda kv: kv[1]):
        print(f"{t:<28} {seen.get(t, 0):>4}/{total[t]:<3} {m*100:>6.0f}%  {'█' * int(m * 10)}")
    print("\nready = you solved the problem last attempt AND can recall it now")
    print(f"overall: {sch.overall_readiness(state, now)*100:.0f}%  (goal {READY_GOAL*100:.0f}%)")


def cmd_stats(args) -> None:
    state = store.load()
    now = sch.utcnow()
    cur, best = sch.streaks(state)
    solved, distinct, proven = sch.solved_counts(state)
    print(f"{BOLD}grind stats{RESET}")
    print(f"streak: {cur}d current (best {best}d)")
    print(f"solved: {solved} attempts · {distinct} distinct problems · {proven} proven (solved last attempt)")
    print(f"interview readiness: {sch.overall_readiness(state, now)*100:.0f}%  "
          f"(goal {READY_GOAL*100:.0f}%)")
    tr = sch.trends(state)
    if tr:
        (r0, r1), (s0, s1), (p0, p1) = tr["rating"], tr["solve_rate"], tr["pace"]
        print("trend (first half -> recent):")
        print(f"  rating      {r0:.2f} -> {r1:.2f}")
        print(f"  solve rate  {s0*100:.0f}% -> {s1*100:.0f}%")
        print(f"  pace        {p0:.2f}x -> {p1:.2f}x of target time")

    act = sch.activity_by_day(state)

    # by difficulty
    bank = sch.bank()
    last_solved: dict[str, bool] = {}
    solved_attempts: dict[str, int] = {}
    for entry in state.get("logs", []):
        last_solved[entry["slug"]] = entry.get("solved", False)
        if entry.get("solved"):
            solved_attempts[entry["slug"]] = solved_attempts.get(entry["slug"], 0) + 1
    print("by difficulty:")
    for diff in ("Easy", "Medium", "Hard"):
        diff_slugs = [p["slug"] for p in bank if p["difficulty"] == diff]
        if not diff_slugs:
            continue
        ready_vals = [sch.readiness(state, s, now) for s in diff_slugs]
        avg_ready = sum(ready_vals) / len(ready_vals) * 100
        proven = sum(1 for s in diff_slugs if last_solved.get(s))
        distinct_solved = sum(1 for s in diff_slugs if s in solved_attempts)
        total_att = sum(solved_attempts.get(s, 0) for s in diff_slugs)
        print(f"  {diff:<6} ready {avg_ready:>5.0f}%  proven {proven:>2}/{len(diff_slugs):<2}  solved {distinct_solved:>2} att {total_att:>3}")
    days = [(now.astimezone().date() - timedelta(days=i)).isoformat() for i in range(13, -1, -1)]
    counts = [act.get(d, 0) for d in days]
    peak = max(counts, default=0)
    bars = " ▁▂▃▄▅▆▇█"
    spark = "".join(bars[1 + int(c / peak * 7)] if c else "·" for c in counts)
    print(f"last 14 days   {spark}")
    print(f"               peak {peak} attempts/day")

    # 12-week heatmap (84 days)
    heatmap_days = [(now.astimezone().date() - timedelta(days=i)).isoformat() for i in range(83, -1, -1)]
    heatmap_counts = [act.get(d, 0) for d in heatmap_days]
    heatmap_peak = max(heatmap_counts, default=0)
    heatmap_bars = " ▁▂▃▄▅▆▇█"
    print()
    print("last 12 weeks:")
    for w in range(12):
        week_counts = heatmap_counts[w*7:(w+1)*7]
        week_start = heatmap_days[w*7]
        week_label = week_start[:10]  # YYYY-MM-DD
        week_bars = "".join(heatmap_bars[1 + int(c / heatmap_peak * 7)] if c and heatmap_peak else "·" for c in week_counts)
        print(f"  {week_label}  {week_bars}")
    if heatmap_peak:
        print(f"               · none {heatmap_bars[1:]} peak {heatmap_peak}/day")


PRESETS = {
    "intensive": {"daily_new": 8, "retention_target": 0.95, "auto_edit": True},
    "casual": {"daily_new": 2, "retention_target": 0.85, "auto_edit": False},
    "maintenance": {"daily_new": 0, "retention_target": 0.9, "auto_edit": False},
}


def cmd_config(args) -> None:
    state = store.load()
    if not args.set:
        for k, v in state["config"].items():
            print(f"{k} = {v}")
        return
    key, _, val = args.set.partition("=")
    key = key.strip()
    # Handle preset=<name>
    if key == "preset":
        if val not in PRESETS:
            sys.exit(f"Unknown preset: {val}. Valid: {', '.join(PRESETS.keys())}")
        for pk, pv in PRESETS[val].items():
            if pk not in state["config"]:
                sys.exit(f"Preset key {pk} not a valid config key")
            # Reuse the same validation logic
            default = state["config"][pk]
            if isinstance(default, bool):
                if str(pv).lower() not in ("true", "false"):
                    sys.exit(f"{pk} must be true or false")
                state["config"][pk] = str(pv).lower() == "true"
            elif isinstance(default, (int, float)):
                state["config"][pk] = pv
            else:
                state["config"][pk] = pv
        store.save(state)
        for pk, pv in PRESETS[val].items():
            print(f"{pk} = {pv}")
        return
    if key not in state["config"]:
        sys.exit(f"Unknown config key: {key}")
    default = state["config"][key]
    if isinstance(default, bool):
        if val.lower() not in ("true", "false"):
            sys.exit(f"{key} must be true or false")
        val = val.lower() == "true"
    elif isinstance(default, (int, float)):
        try:
            val = int(val) if val.lstrip("-").isdigit() else float(val)
        except ValueError:
            sys.exit(f"{key} must be a number, got {val!r}")
    state["config"][key] = val
    store.save(state)
    print(f"{key} = {val}")


# ---------------------------------------------------------------- backup
# Invisible by design: every `grind done` commits progress + solutions to a
# local history repo. Cloud push happens automatically once the user names a
# repo (asked once, on first boot — never created for them). Success prints
# nothing; errors print one line and never block grading.

def _git(repo: Path, *args: str) -> tuple[bool, str]:
    try:
        r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    except FileNotFoundError:
        return False, "git not found — install git first"
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def _run(cmd: list[str]) -> tuple[bool, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        return False, ""
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def _ask_repo() -> str | None:
    """First-boot question: where should backups be pushed? Any git remote."""
    try:
        ans = input("\nWhere should grind back up your progress?\n"
                    "  - your backup repo's git url — any host works, e.g.\n"
                    "      git@github.com:you/grind-backup.git  https://gitlab.com/you/x.git\n"
                    "      ssh://your-server/~/grind-backup.git  or a path like /mnt/nas/grind.git\n"
                    "    (create it yourself — grind never makes repos for you)\n"
                    "  - your existing backup's url, if you already use grind on another machine\n"
                    "  - or press Enter to keep backups local-only: ").strip()
    except (EOFError, KeyboardInterrupt, OSError):
        return None
    return ans or None


def _save_remote(state: dict, ans: str) -> str | None:
    """Store the user's remote answer. Accepts anything git can push to
    (url, scp-style, or local path); bare words are rejected with a hint.
    Returns the stored url, or None if the answer wasn't usable."""
    ans = ans.strip()
    if any(c in ans for c in "/@:"):
        state["config"]["backup_remote"] = ans
        return ans
    print("  that doesn't look like a git url — try something like "
          "git@host:you/repo.git, https://host/you/repo.git, or /path/to/repo.git")
    return None


def _restore_if_grind_repo(repo_url: str) -> bool:
    """On first boot: if the named repo already holds a grind backup, pull it.
    Returns True when local state was replaced by the backup."""
    ok, _ = _run(["git", "ls-remote", repo_url, "HEAD"])
    if not ok:
        print(f"  noted — grind will back up to {repo_url} once the repo exists "
              "(create it on your git host, e.g. as a private repo)")
        return False
    repo = store.data_dir() / "repo"
    repo.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["git", "clone", "-q", repo_url, str(repo)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  couldn't read that repo ({(r.stderr or r.stdout).strip()})")
        return False
    if not (repo / "state.json").exists():
        return False  # repo exists but holds no grind backup — future pushes will use it
    shutil.copy2(repo / "state.json", store.state_path())
    sol = Path(os.environ.get("GRIND_SOLUTIONS", "solutions"))
    if (repo / "solutions").exists():
        if sol.exists():
            shutil.rmtree(sol)
        shutil.copytree(repo / "solutions", sol)
    return True


def _do_backup(state: dict) -> dict:
    """Commit state + solutions to the local history repo (always) and push to
    the cloud remote when one resolves. Returns
    {committed, pushed, remote, error} and is silent on success."""
    repo = store.data_dir() / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    res = {"committed": False, "pushed": False, "remote": None, "error": None}
    if not (repo / ".git").exists():
        ok, err = _git(repo, "init", "-b", "main")
        if not ok:
            ok, err = _git(repo, "init")
        if not ok:
            res["error"] = err
            return res
    shutil.copy2(store.state_path(), repo / "state.json")
    src = Path(os.environ.get("GRIND_SOLUTIONS", "solutions"))
    if src.exists():
        dst = repo / "solutions"
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    ok, err = _git(repo, "add", "-A")
    if not ok:
        res["error"] = err
        return res
    ok, out_ = _git(repo, "status", "--porcelain")
    if out_:
        ready = sch.overall_readiness(state, sch.utcnow()) * 100
        msg = (f"grind backup {sch.utcnow():%Y-%m-%d %H:%M} — "
               f"readiness {ready:.0f}%, {len(state['logs'])} reviews")
        ok, err = _git(repo, "commit", "-m", msg)
        if not ok:
            res["error"] = err
            return res
        res["committed"] = True

    # a configured remote means push even without new commits — an explicit
    # `grind backup` must always bring the cloud up to date
    remote = state["config"].get("backup_remote")
    if not remote:
        if not state.get("hinted_cloud"):
            state["hinted_cloud"] = True  # one-time nudge, then silence forever
            print("  backup: local only — run `grind backup` once to pick a backup repo (any git remote)")
        return res
    ok, has_commits = _git(repo, "log", "-1", "--oneline")
    if not ok:
        return res  # nothing to push yet (no history at all)

    res["remote"] = remote
    _git(repo, "remote", "remove", "origin")
    ok, err = _git(repo, "remote", "add", "origin", remote)
    if not ok:
        res["error"] = err
        return res
    ok, err = _git(repo, "push", "-u", "origin", "HEAD:main")
    if not ok:
        hint = (" — create the repo first (on github.com), then grind backup"
                if "not found" in err.lower() else "")
        res["error"] = f"push failed: {err}{hint}"
        return res
    res["pushed"] = True
    return res


def cmd_backup(args) -> None:
    state = store.load()
    if args.remote:
        state["config"]["backup_remote"] = args.remote
    elif not state["config"].get("backup_remote"):
        ans = _ask_repo()               # skipped or missed on first boot
        if ans:
            _save_remote(state, ans)
    res = _do_backup(state)
    store.save(state)
    if res["error"]:
        sys.exit(f"backup failed: {res['error']}")
    where = res["remote"] or f"local history ({store.data_dir() / 'repo'})"
    print("backed up — " + where if res["pushed"] or res["committed"]
          else "no new changes — " + where)


def cmd_restore(args) -> None:
    state = store.load()
    url = args.url or state["config"].get("backup_remote")
    if not url:
        ans = _ask_repo()
        if ans:
            url = _save_remote(state, ans)
    if not url:
        sys.exit("no backup to restore from — pass a repo url, or pick one "
                 "with `grind backup` first")
    repo = store.data_dir() / "repo"
    if (repo / ".git").exists():
        ok, err = _git(repo, "pull", "--ff-only")
        if not ok:
            sys.exit(f"pull failed: {err}")
    else:
        repo.parent.mkdir(parents=True, exist_ok=True)
        try:
            r = subprocess.run(["git", "clone", url, str(repo)],
                               capture_output=True, text=True)
        except FileNotFoundError:
            sys.exit("git not found — install git first")
        if r.returncode != 0:
            sys.exit(f"clone failed: {(r.stdout + r.stderr).strip()}")
    if (repo / "state.json").exists():
        if store.state_path().exists() and not args.force:
            sys.exit("local state already exists — pass --force to overwrite it with the backup")
        shutil.copy2(repo / "state.json", store.state_path())
    sol = Path(os.environ.get("GRIND_SOLUTIONS", "solutions"))
    if (repo / "solutions").exists():
        if sol.exists():
            shutil.rmtree(sol)
        shutil.copytree(repo / "solutions", sol)
    state = store.load()
    ready = sch.overall_readiness(state, sch.utcnow()) * 100
    print(f"restored from {url} — readiness {ready:.0f}%, {len(state['logs'])} reviews, "
          f"{len(state['cards'])} problems seen")

# ---------------------------------------------------------------- completion

def _completion_data() -> dict:
    """Return all completion-relevant data as a dict (single source of truth)."""
    from .scheduler import bank

    problems = bank()
    slugs = [p["slug"] for p in problems]

    # Build subcommand -> flags map from the parser structure
    # We reconstruct it here to keep it in sync with main()
    subcommands = {
        "next": ["--web", "--edit", "--ahead", "--new"],
        "help": [],
        "pause": [],
        "edit": [],
        "web": [],
        "log": ["--n", "--all"],
        "list": ["--topic", "--due", "--new", "--proven"],
        "done": ["--solved", "--fail", "--rating", "--mins"],
        "skip": [],
        "check": ["--n", "--all"],
        "reference": [],
        "extras": [],
        "status": [],
        "topics": [],
        "stats": [],
        "config": [],
        "backup": ["--remote"],
        "restore": ["--force"],
        "update": [],
        "completion": [],
        "redo": [],
    }

    # Global flags (always available)
    global_flags = ["--version", "--help"]

    # Config keys
    config_keys = [
        "daily_new",
        "retention_target",
        "auto_web",
        "auto_edit",
        "backup_remote",
        "update_check",
    ]

    return {
        "subcommands": subcommands,
        "slugs": slugs,
        "global_flags": global_flags,
        "config_keys": config_keys,
    }


def cmd__completion_data(args) -> None:
    """Internal: print completion data as JSON."""
    import json
    print(json.dumps(_completion_data()))


def _completion_script_bash(data: dict) -> str:
    lines = [
        "# grind bash completion",
        "# Source this file or run: grind completion bash > /path/to/completion",
        "",
        "_grind_completions() {",
        "    local cur prev words cword",
        "    _init_completion || return",
        "    local subcommands=\"{}\"".format(" ".join(sorted(data["subcommands"].keys()))),
        "    local slugs=\"{}\"".format(" ".join(data["slugs"])),
        "    local config_keys=\"{}\"".format(" ".join(data["config_keys"])),
        "",
        "    if [[ $cword -eq 1 ]]; then",
        "        COMPREPLY=($(compgen -W \"$subcommands\" -- \"$cur\"))",
        "        return",
        "    fi",
        "",
        "    local cmd=\"${words[1]}\"",
        "    case \"$cmd\" in",
        "        check|reference|extras|redo)",
        "            COMPREPLY=($(compgen -W \"$slugs\" -- \"$cur\"))",
        "            ;;",
        "        config)",
        "            COMPREPLY=($(compgen -W \"$config_keys\" -- \"$cur\"))",
        "            ;;",
        "        completion)",
        "            COMPREPLY=($(compgen -W \"bash zsh fish\" -- \"$cur\"))",
        "            ;;",
        "        list)",
        "            local list_flags=\"--topic --due --new --proven\"",
        "            COMPREPLY=($(compgen -W \"$list_flags\" -- \"$cur\"))",
        "            ;;",
        "        log)",
        "            local log_flags=\"--n --all\"",
        "            COMPREPLY=($(compgen -W \"$log_flags\" -- \"$cur\"))",
        "            ;;",
        "        done)",
        "            local done_flags=\"--solved --fail --rating --mins\"",
        "            COMPREPLY=($(compgen -W \"$done_flags\" -- \"$cur\"))",
        "            ;;",
        "        backup)",
        "            local backup_flags=\"--remote\"",
        "            COMPREPLY=($(compgen -W \"$backup_flags\" -- \"$cur\"))",
        "            ;;",
        "        restore)",
        "            local restore_flags=\"--force\"",
        "            COMPREPLY=($(compgen -W \"$restore_flags\" -- \"$cur\"))",
        "            ;;",
        "        next)",
        "            local next_flags=\"--web --edit --ahead --new\"",
        "            COMPREPLY=($(compgen -W \"$next_flags\" -- \"$cur\"))",
        "            ;;",
        "        *)",
        "            local all_flags=\"{}\"".format(" ".join(data["global_flags"])),
        "            COMPREPLY=($(compgen -W \"$all_flags\" -- \"$cur\"))",
        "            ;;",
        "    esac",
        "}",
        "",
        "complete -F _grind_completions grind",
    ]
    return "\n".join(lines)


def _completion_script_zsh(data: dict) -> str:
    lines = [
        "#compdef grind",
        "# grind zsh completion",
        "# Source this file or run: grind completion zsh > /path/to/_grind",
        "",
        "_grind() {",
        "    local -a subcommands",
        "    local -a slugs",
        "    local -a config_keys",
        "    local -a global_flags",
        "",
        "    subcommands=({})".format(" ".join(f"'{s}'" for s in sorted(data["subcommands"].keys()))),
        "    slugs=({})".format(" ".join(f"'{s}'" for s in data["slugs"])),
        "    config_keys=({})".format(" ".join(f"'{s}'" for s in data["config_keys"])),
        "    global_flags=({})".format(" ".join(f"'{s}'" for s in data["global_flags"])),
        "",
        "    local context state state_descr line",
        "    declare -A opt_args",
        "",
        "    _arguments -C \\",
        "        '($global_flags)'{$global_flags}'[Global options]' \\",
        "        '1: :($subcommands)' \\",
        "        '*::arg:->args'",
        "",
        "    case $state in",
        "        (subcmds)",
        "            _describe 'subcommand' subcommands",
        "            ;;",
        "        (args)",
        "            case $line[1] in",
        "                (check|reference|extras|redo)",
        "                    _values 'problem' $slugs",
        "                    ;;",
        "                (config)",
        "                    _values 'config key' $config_keys",
        "                    ;;",
        "                (completion)",
        "                    _values 'shell' 'bash' 'zsh' 'fish'",
        "                    ;;",
        "                (list)",
        "                    _arguments '--topic[Filter by topic substring]' '--due[Show only due problems]' '--new[Show only new problems]' '--proven[Show only proven problems]'",
        "                    ;;",
        "                (log)",
        "                    _arguments '--n[Show last N entries]' '--all[Show all entries]'",
        "                    ;;",
        "                (done)",
        "                    _arguments '--solved[You solved it]' '--fail[You did not solve it]' '--rating[Override rating (1..4)]' '--mins[Override elapsed time (minutes)]'",
        "                    ;;",
        "                (backup)",
        "                    _arguments '--remote[Git URL to back up to]'",
        "                    ;;",
        "                (restore)",
        "                    _arguments '--force[Overwrite existing local state]'",
        "                    ;;",
        "                (next)",
        "                    _arguments '--web[Open in browser]' '--edit[Open in editor]' '--ahead[Pull next review early]' '--new[Pick a new problem]'",
        "                    ;;",
        "                (*)",
        "                    _arguments $global_flags",
        "                    ;;",
        "            esac",
        "            ;;",
        "    esac",
        "}",
        "",
        "compdef _grind grind",
    ]
    return "\n".join(lines)


def _completion_script_fish(data: dict) -> str:
    lines = [
        "# grind fish completion",
        "# Source this file or run: grind completion fish > ~/.config/fish/completions/grind.fish",
        "",
        "complete -c grind -f -a '({})'".format(" ".join(sorted(data["subcommands"].keys()))),
        "",
    ]
    # Subcommand-specific completions
    for cmd, flags in data["subcommands"].items():
        if flags:
            lines.append("complete -c grind -f -n '__fish_use_subcommand {}' -a '{}'".format(
                cmd, " ".join(flags)))
    # Slug completions for commands that take a slug
    slug_cmds = ["check", "reference", "extras", "redo"]
    for cmd in slug_cmds:
        lines.append("complete -c grind -f -n '__fish_use_subcommand {}' -a '{}'".format(
            cmd, " ".join(f"'{s}'" for s in data["slugs"])))
    # Config keys
    lines.append("complete -c grind -f -n '__fish_use_subcommand config' -a '{}'".format(
        " ".join(f"'{k}'" for k in data["config_keys"])))
    return "\n".join(lines)


def cmd_completion(args) -> None:
    """Print shell completion script for bash, zsh, or fish."""
    data = _completion_data()
    if args.shell == "bash":
        print(_completion_script_bash(data))
    elif args.shell == "zsh":
        print(_completion_script_zsh(data))
    elif args.shell == "fish":
        print(_completion_script_fish(data))


# ---------------------------------------------------------------- redo

def cmd_redo(args) -> None:
    """Mark a problem as due now for immediate re-attempt."""
    import sys
    from . import scheduler as sch
    from . import store

    state = store.load()
    slug = args.slug

    # Resolve slug: arg -> active session -> last graded
    if not slug:
        sess = state.get("session") or {}
        slug = sess.get("slug")
    if not slug and state.get("logs"):
        slug = state["logs"][-1]["slug"]
    if not slug:
        sys.exit("pass a problem id (e.g. 'two-sum'), run during an active session, or grade something first")

    # Validate slug exists in bank
    by_slug_map = {p["slug"]: p for p in sch.bank()}
    if slug not in by_slug_map:
        sys.exit(f"unknown problem: {slug}")

    prob = by_slug_map[slug]
    now = sch.utcnow()

    # Mark as due now
    if not sch.mark_due_now(state, slug, now):
        sys.exit("problem not seen yet — use 'grind next --new' to learn it")

    store.save(state)
    print(f"Redo queued: {prob['title']} — grind next will pick it immediately")
# ---------------------------------------------------------------- entry

def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="grind", description="FSRS-driven LeetCode fluency trainer")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("next", help="present the best next problem and start the timer")
    p.add_argument("--web", action="store_true", help="open the problem in your browser")
    p.add_argument("--edit", action="store_true", help="open the scaffold in $EDITOR")
    p.add_argument("--ahead", action="store_true", help="pull the next review early (ignore due date)")
    p.add_argument("--new", action="store_true", help="pick a new problem (ignore daily limit)")
    p.set_defaults(fn=cmd_next)
    p = sub.add_parser("help", help="show this friendly command overview")
    p.set_defaults(fn=cmd_help)
    p = sub.add_parser("pause", help="pause the active session timer")
    p.set_defaults(fn=cmd_pause)
    p = sub.add_parser("edit", help="open active session's scaffold in $EDITOR")
    p.set_defaults(fn=cmd_edit)
    p = sub.add_parser("web", help="open active session's LeetCode page in browser")
    p.set_defaults(fn=cmd_web)
    p = sub.add_parser("log", help="show recent graded attempts")
    p.add_argument("--n", type=int, help="show last N entries (default 20)")
    p.add_argument("--all", action="store_true", help="show all entries")
    p.set_defaults(fn=cmd_log)
    p = sub.add_parser("list", help="list all problems with status (new/due/seen/proven)")
    p.add_argument("--topic", help="filter by topic substring")
    p.add_argument("--due", action="store_true", help="show only due problems")
    p.add_argument("--new", action="store_true", help="show only new (unseen) problems")
    p.add_argument("--proven", action="store_true", help="show only proven problems")
    p.add_argument("--difficulty", choices=["Easy", "Medium", "Hard"], help="filter by difficulty")
    p.set_defaults(fn=cmd_list)
    p = sub.add_parser("upcoming", help="show reviews due in the next N days")
    p.add_argument("--days", type=int, default=14, help="look ahead N days (default 14)")
    p.set_defaults(fn=cmd_upcoming)
    p = sub.add_parser("done", help="stop timer, grade, schedule next rep")
    p.add_argument("--solved", action="store_true", default=None, help="you solved it (skips prompt)")
    p.add_argument("--fail", dest="solved", action="store_false", default=None, help="you did not solve it")
    p.add_argument("--rating", type=float, help="override rating directly (float 1..4)")
    p.add_argument("--mins", type=float, help="override elapsed time (minutes)")
    p.set_defaults(fn=cmd_done, solved=None)
    p = sub.add_parser("skip", help="drop the active session without grading")
    p.set_defaults(fn=cmd_skip)
    p = sub.add_parser("check", help="quick subset of TESTS (default 3; grind done runs all)")
    p.add_argument("slug", nargs="?", help="defaults to the active session's problem")
    p.add_argument("--n", type=int, help="run the first N case(s)")
    p.add_argument("--all", action="store_true", help="run the full set")
    p.set_defaults(fn=cmd_check)
    p = sub.add_parser("review", help="run full test suite for a problem without grading (no FSRS impact)")
    p.add_argument("slug", nargs="?", help="defaults to the active session's problem")
    p.set_defaults(fn=cmd_review)
    p = sub.add_parser("reference", help="print this problem's verified reference solution — how each edge case's expected value was computed")
    p.add_argument("slug", nargs="?", help="defaults to the active session's problem")
    p.set_defaults(fn=cmd_reference)
    p = sub.add_parser("extras", help="print the hand-written edge cases `grind done`'s full suite runs")
    p.add_argument("slug", nargs="?", help="defaults to the active session's problem")
    p.set_defaults(fn=cmd_extras)
    p = sub.add_parser("status", help="one-line progress snapshot")
    p.set_defaults(fn=cmd_status)
    p = sub.add_parser("topics", help="per-topic interview-readiness breakdown")
    p.set_defaults(fn=cmd_topics)
    p = sub.add_parser("stats", help="streaks, solved counts, trends, activity")
    p.set_defaults(fn=cmd_stats)
    p = sub.add_parser("config", help="show or set config (key=value)")
    p.add_argument("set", nargs="?", help="e.g. daily_new=3")
    p.set_defaults(fn=cmd_config)
    p = sub.add_parser("backup", help="back up now (automatic after every grind done anyway)")
    p.add_argument("--remote", help="git url to back up to from now on (e.g. your private GitHub repo)")
    p.set_defaults(fn=cmd_backup)
    p = sub.add_parser("restore", help="pull your backup onto this machine (new-machine bootstrap)")
    p.add_argument("url", nargs="?", help="backup repo url (defaults to backup_remote)")
    p.add_argument("--force", action="store_true", help="overwrite existing local state")
    p.set_defaults(fn=cmd_restore)
    # completion subcommand (hidden _completion_data for internal use)
    p = sub.add_parser("completion", help="print shell completion script (bash|zsh|fish)")
    p.add_argument("shell", choices=["bash", "zsh", "fish"], help="target shell")
    p.set_defaults(fn=cmd_completion)
    p = sub.add_parser("_completion_data", help=argparse.SUPPRESS)
    p.set_defaults(fn=cmd__completion_data)

    # redo subcommand
    p = sub.add_parser("redo", help="mark a problem as due now for immediate re-attempt")
    p.add_argument("slug", nargs="?", help="problem slug (defaults to active session or last graded)")
    p.set_defaults(fn=cmd_redo)

    p = sub.add_parser("update", help="pull the latest version and reinstall (refuses a dirty tree)")
    p.set_defaults(fn=update.cmd_update)
    ap.add_argument("--version", action="version", version=f"grind {__version__}")
    args = ap.parse_args(argv)
    if not getattr(args, "fn", None):
        args = ap.parse_args(["next"], namespace=args)
    args.fn(args)
    update.maybe_check()

if __name__ == "__main__":
    main()
