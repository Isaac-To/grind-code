"""grind — FSRS-driven LeetCode fluency trainer.

Loop:  grind next   -> presents the best problem, writes a scaffold, starts timer
       grind done   -> stop timer, grade from time+outcome, FSRS schedules the next rep
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import types
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path

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


def start_session(state: dict, prob: dict, why: str) -> None:
    now = sch.utcnow()
    sol_dir = Path(os.environ.get("GRIND_SOLUTIONS", "solutions"))
    sol_dir.mkdir(parents=True, exist_ok=True)
    scaffold = sol_dir / f"{prob['slug']}.py"
    target, phase = sch.target_info(state, prob)
    entry = problems.get(prob["slug"])
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
    print("  solve it in your IDE, verify with `grind check`, then grade with `grind done`")


def cmd_next(args) -> None:
    state = store.load()
    if state["session"]:
        p = sch.by_slug()[state["session"]["slug"]]
        el = (sch.utcnow() - datetime.fromisoformat(state["session"]["started"])).total_seconds() / 60
        print(f"Session already active: {p['title']}  ({_fmt_min(el)} elapsed)")
        print("Finish it first:  grind done  /  grind skip")
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
    prob, why = sch.pick_next(state, now)
    if prob is None:
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


def cmd_done(args) -> None:
    state = store.load()
    sess = state["session"]
    if not sess:
        sys.exit("No active session. Start one with: grind next")
    prob = sch.by_slug()[sess["slug"]]
    now = sch.utcnow()
    elapsed = args.mins if args.mins is not None else \
        (now - datetime.fromisoformat(sess["started"])).total_seconds() / 60
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
    res = _do_backup(state)
    store.save(state)  # persist backup flags mutated during the silent backup
    if res["error"]:
        print(f"  backup: {res['error']}")
    print("Next: grind next")


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
    if not state["session"]:
        sys.exit("No active session.")
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
    days = [(now.astimezone().date() - timedelta(days=i)).isoformat() for i in range(13, -1, -1)]
    counts = [act.get(d, 0) for d in days]
    peak = max(counts, default=0)
    bars = " ▁▂▃▄▅▆▇█"
    spark = "".join(bars[1 + int(c / peak * 7)] if c else "·" for c in counts)
    print(f"last 14 days   {spark}")
    print(f"               peak {peak} attempts/day")

def cmd_config(args) -> None:
    state = store.load()
    if not args.set:
        for k, v in state["config"].items():
            print(f"{k} = {v}")
        return
    key, _, val = args.set.partition("=")
    key = key.strip()
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

# ---------------------------------------------------------------- entry

def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="grind", description="FSRS-driven LeetCode fluency trainer")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("next", help="present the best next problem and start the timer")
    p.add_argument("--web", action="store_true", help="open the problem in your browser")
    p.add_argument("--edit", action="store_true", help="open the scaffold in $EDITOR")
    p.set_defaults(fn=cmd_next)
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
    args = ap.parse_args(argv)
    if not getattr(args, "fn", None):
        args = ap.parse_args(["next"], namespace=args)
    args.fn(args)


if __name__ == "__main__":
    main()
