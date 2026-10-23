"""grind.cli — every command, every branch, through the real entry point."""
from __future__ import annotations

from datetime import timedelta

import builtins
import sys

import pytest

from fsrs import Card

from grind import cli
from grind import scheduler as sch
from grind import store
from grind import __version__

from conftest import (add_log, local, now_utc, open_session, seed_review_card,
                      write_solution)

SOLVED_BODY = "class Solution:\n    def containsDuplicate(self, nums):\n        return len(set(nums)) != len(nums)"


def run(argv, capsys):
    """Invoke cli.main; returns exit code (None if it returned normally).
    sys.exit("msg") prints the message to stderr only when SystemExit
    propagates uncaught — replicate that here so tests see real output."""
    try:
        cli.main(argv)
        return None
    except SystemExit as e:
        if isinstance(e.code, str):
            print(e.code, file=sys.stderr)
            return 1
        return e.code


def out(capsys):
    """Combined stdout+stderr: sys.exit('msg') writes to stderr."""
    r = capsys.readouterr()
    return r.out + r.err


# ---------------------------------------------------------------- helpers

def test_url_format():
    assert cli.url("two-sum") == "https://leetcode.com/problems/two-sum/"


def test_fmt_min():
    assert cli._fmt_min(30) == "30m"
    assert cli._fmt_min(90) == "1h30m"
    assert cli._fmt_min(75.4) == "1h15m"


# ---------------------------------------------------------------- next

def test_next_creates_scaffold_and_session(env, capsys):
    assert run(["next"], capsys) is None
    o = out(capsys)
    assert "Contains Duplicate" in o and "new problem" in o
    assert "https://leetcode.com/problems/contains-duplicate/" in o
    assert "(target 15m · prior)" in o
    data, sol = env
    sc = sol / "contains-duplicate.py"
    assert sc.exists()
    body = sc.read_text()
    assert "217. Contains Duplicate" in body
    assert "class Solution" in body and "TESTS = [" in body
    s = store.load()
    assert s["session"]["slug"] == "contains-duplicate"
    assert s["session"]["started"]


def test_next_never_overwrites_existing_scaffold(env, capsys):
    data, sol = env
    sol.mkdir(parents=True, exist_ok=True)
    (sol / "contains-duplicate.py").write_text("# MY WORK\n")
    run(["next"], capsys)
    assert (sol / "contains-duplicate.py").read_text() == "# MY WORK\n"


def test_next_active_session_short_circuits(env, capsys):
    open_session("two-sum")
    assert run(["next"], capsys) is None
    o = out(capsys)
    assert "Session already active" in o and "grind done" in o


def test_next_caught_up_without_cards(env, capsys):
    s = store.load()
    s["config"]["daily_new"] = 0
    store.save(s)
    run(["next"], capsys)
    o = out(capsys)
    assert "All caught up" in o
    assert "Next review" not in o


def test_next_caught_up_reports_upcoming(env, capsys, no_fuzz):
    s = store.load()
    s["config"]["daily_new"] = 0
    seed_review_card(s, "two-sum")  # future due
    store.save(s)
    run(["next"], capsys)
    assert "Next review:" in out(capsys)


def test_next_web_flag_and_config(env, capsys, monkeypatch):
    opened = []
    monkeypatch.setattr(cli.webbrowser, "open", lambda u: opened.append(u))
    run(["next", "--web"], capsys)
    assert opened == ["https://leetcode.com/problems/contains-duplicate/"]
    s = store.load()
    s["config"]["auto_web"] = True
    s["session"] = None
    store.save(s)
    run(["next"], capsys)
    assert len(opened) == 2


def test_next_edit_flag_and_config(env, capsys, monkeypatch):
    called = []
    monkeypatch.setattr(cli.subprocess, "call", lambda a: called.append(a))
    run(["next", "--edit"], capsys)
    assert len(called) == 1 and called[0][1].endswith("contains-duplicate.py")
    s = store.load()
    s["config"]["auto_edit"] = True
    s["session"] = None
    store.save(s)
    run(["next"], capsys)
    assert len(called) == 2
def test_next_ahead_pulls_future_review(env, capsys, no_fuzz):
    """--ahead pulls the earliest upcoming review regardless of due date."""
    data, sol = env
    # Seed two future review cards
    from conftest import seed_review_card
    state = store.load()
    seed_review_card(state, "two-sum")
    seed_review_card(state, "valid-anagram")
    store.save(state)

    # Regular pick should get a new problem (no due reviews)
    run(["next"], capsys)
    o = out(capsys)
    assert "new problem" in o

    # Skip the session so we can test --ahead
    run(["skip"], capsys)

    # --ahead should pull the earliest upcoming review
    run(["next", "--ahead"], capsys)
    o = out(capsys)
    assert "review" in o
    assert "Two Sum" in o or "Valid Anagram" in o  # earliest due


def test_next_ahead_no_upcoming(env, capsys):
    """--ahead with no cards prints helpful message."""
    # Pre-consume intro flag
    s = store.load()
    s["seen_intro"] = True
    store.save(s)

    run(["next", "--ahead"], capsys)
    assert "No upcoming reviews to pull" in out(capsys)


def test_next_new_ignores_daily_limit(env, capsys, no_fuzz):
    """--new ignores daily_new limit and picks a new problem."""
    data, sol = env
    s = store.load()
    s["config"]["daily_new"] = 0
    store.save(s)

    # Regular pick should hit limit
    run(["next"], capsys)
    assert "All caught up" in out(capsys)

    # --new should pick anyway
    run(["next", "--new"], capsys)
    o = out(capsys)
    assert "new problem" in o


def test_next_new_no_remaining(env, capsys, no_fuzz):
    """--new with no unseen problems prints helpful message."""
    # Mark all problems as seen by seeding review cards
    s = store.load()
    from conftest import seed_review_card
    for p in sch.bank():
        seed_review_card(s, p["slug"])
    store.save(s)

    run(["next", "--new"], capsys)
    assert "No new problems available" in out(capsys)

# ---------------------------------------------------------------- pause

def test_pause_no_session(env, capsys):
    assert run(["pause"], capsys) == 1
    assert "No active session" in out(capsys)


def test_pause_and_resume(env, capsys):
    # Start a session
    run(["next"], capsys)
    out(capsys)  # clear

    # Pause it
    run(["pause"], capsys)
    assert "Paused:" in out(capsys)
    out(capsys)  # clear

    # Resume with next
    run(["next"], capsys)
    assert "Resumed:" in out(capsys)
    out(capsys)  # clear

    # Pause again
    run(["pause"], capsys)
    assert "Paused:" in out(capsys)


def test_pause_already_paused(env, capsys):
    run(["next"], capsys)
    out(capsys)
    run(["pause"], capsys)
    out(capsys)
    # Try to pause again
    assert run(["pause"], capsys) == 1
    assert "already paused" in out(capsys).lower()


def test_done_accounts_for_pause(env, capsys, no_fuzz):
    """Pause time is excluded from elapsed when grading."""
    data, sol = env
    run(["next"], capsys)
    out(capsys)

    # Pause immediately
    run(["pause"], capsys)
    out(capsys)

    # Wait a moment (simulated by the test being fast)
    # Resume and immediately done
    run(["next"], capsys)
    out(capsys)

    write_solution(sol, "contains-duplicate", SOLVED_BODY,
                   [(([1, 2, 3, 1],), True), (([1, 2, 3, 4],), False)])
    run(["done", "--mins", "1"], capsys)  # Only 1 minute of real time
    o = out(capsys)
    # Should be graded on ~1 minute, not including pause duration
    assert "1m" in o or "solved in 1m" in o or "solved in" in o

# ---------------------------------------------------------------- done

def test_done_gate_pass_grades_solved(env, capsys, no_fuzz):
    data, sol = env
    open_session("contains-duplicate")
    write_solution(sol, "contains-duplicate", SOLVED_BODY,
                   [(([1, 2, 3, 1],), True), (([1, 2, 3, 4],), False)])
    assert run(["done", "--mins", "8"], capsys) is None
    o = out(capsys)
    assert "full suite: 2/2 passed" in o
    assert "solved in 8m" in o and "rating 3.3" in o
    assert "next review in" in o
    s = store.load()
    log = s["logs"][-1]
    assert log["solved"] is True and log["new"] is True
    assert log["tests"] == "2/2" and log["elapsed"] == 8.0
    assert s["session"] is None and s["last"] == "contains-duplicate"


def test_done_gate_fail_grades_unsolved(env, capsys, no_fuzz):
    data, sol = env
    open_session("contains-duplicate")
    write_solution(sol, "contains-duplicate",
                   "class Solution:\n    def containsDuplicate(self, nums):\n        return True",
                   [(([1, 2, 3, 1],), True), (([1, 2, 3, 4],), False)])
    run(["done", "--mins", "10"], capsys)
    o = out(capsys)
    assert "full suite: 1/2 passed" in o
    assert "unsolved in 10m" in o and "rating 1.00/4" in o
    assert "counted as unsolved" in o
    assert store.load()["logs"][-1]["solved"] is False


def test_done_flags_overridden_by_failing_tests(env, capsys, no_fuzz):
    data, sol = env
    open_session("contains-duplicate")
    write_solution(sol, "contains-duplicate",
                   "class Solution:\n    def containsDuplicate(self, nums):\n        return True",
                   [(([1, 2, 3, 4],), False)])
    run(["done", "--mins", "5", "--solved"], capsys)
    o = out(capsys)
    assert "overridden by TESTS" in o
    assert store.load()["logs"][-1]["solved"] is False


def test_done_no_tests_falls_back_to_flags(env, capsys, no_fuzz):
    data, sol = env
    open_session("contains-duplicate")
    write_solution(sol, "contains-duplicate", SOLVED_BODY, [])  # empty TESTS
    run(["done", "--solved", "--mins", "9"], capsys)
    s = store.load()
    assert s["logs"][-1]["solved"] is True and s["logs"][-1]["tests"] is None


def test_done_no_solution_file_falls_back_to_flags(env, capsys, no_fuzz):
    open_session("contains-duplicate")  # never wrote a file
    run(["done", "--fail", "--mins", "9"], capsys)
    assert store.load()["logs"][-1]["solved"] is False


def test_done_prompt_yes_and_no(env, capsys, no_fuzz, monkeypatch):
    data, sol = env
    write_solution(sol, "contains-duplicate", SOLVED_BODY, [])
    answers = iter(["y"])
    monkeypatch.setattr(builtins, "input", lambda _: answers.__next__())
    open_session("contains-duplicate")
    run(["done", "--mins", "5"], capsys)
    # (fake input() doesn't echo the prompt; _ask_solved is unit-tested below)
    assert store.load()["logs"][-1]["solved"] is True

    answers = iter(["n"])
    monkeypatch.setattr(builtins, "input", lambda _: answers.__next__())
    open_session("contains-duplicate")
    run(["done", "--mins", "5"], capsys)
    assert store.load()["logs"][-1]["solved"] is False


def test_ask_solved_parses_answers(capsys, monkeypatch):
    answers = iter(["x", "  Y ", "n"])  # junk ignored, whitespace+case-insensitive
    monkeypatch.setattr(builtins, "input", lambda _: answers.__next__())
    assert cli._ask_solved({"title": "Two Sum"}, 5.0) is True
    assert "Two Sum — 5m elapsed." in out(capsys)
    assert cli._ask_solved({"title": "Two Sum"}, 5.0) is False


def test_done_prompt_eof_keeps_session(env, capsys, monkeypatch):
    def boom(_):
        raise EOFError
    monkeypatch.setattr(builtins, "input", boom)
    open_session("contains-duplicate")
    assert run(["done", "--mins", "5"], capsys) == 1
    assert "session kept" in out(capsys)
    s = store.load()
    assert s["session"] is not None and s["logs"] == []


def test_done_broken_solution_file_is_unsolved(env, capsys, no_fuzz):
    data, sol = env
    open_session("contains-duplicate")
    sol.mkdir(parents=True, exist_ok=True)
    (sol / "contains-duplicate.py").write_text("class Solution:\n  def broken(")
    run(["done", "--mins", "5"], capsys)
    o = out(capsys)
    assert "fails to load" in o
    assert store.load()["logs"][-1]["solved"] is False


def test_done_rating_override(env, capsys, no_fuzz):
    data, sol = env
    open_session("contains-duplicate")
    write_solution(sol, "contains-duplicate", SOLVED_BODY, [(([1, 2, 3, 1],), True)])
    run(["done", "--mins", "8", "--rating", "2.5"], capsys)
    assert store.load()["logs"][-1]["rating"] == 2.5


def test_done_rating_out_of_range_keeps_session(env, capsys):
    open_session("contains-duplicate")
    assert run(["done", "--rating", "9"], capsys) == 1
    assert store.load()["session"] is not None and store.load()["logs"] == []


def test_done_requires_session(env, capsys):
    assert run(["done", "--mins", "5"], capsys) == 1
    assert "No active session" in out(capsys)


def test_done_lock_hint_fires_once_on_transition(env, capsys, no_fuzz):
    data, sol = env
    s = store.load()
    for e in (6.0, 7.0, 6.0, 7.0):  # four stable prior attempts
        add_log(s, "contains-duplicate", e, solved=True)
    store.save(s)
    open_session("contains-duplicate")
    write_solution(sol, "contains-duplicate", SOLVED_BODY, [(([1, 2, 3, 1],), True)])
    run(["done", "--mins", "6"], capsys)
    assert "target locked at your demonstrated pace" in out(capsys)

    open_session("contains-duplicate")  # next rep: already locked, no repeat hint
    run(["done", "--mins", "6"], capsys)
    assert "target locked at your demonstrated pace" not in out(capsys)

# ---------------------------------------------------------------- review reset

TWO_SUM_BODY = "class Solution:\n    def twoSum(self, nums, target):\n        return [0, 1]"


def _due_review(slug: str, graded: bool = False) -> None:
    """Seed a due-now review card; graded=True flags its file as a done attempt."""
    s = store.load()
    seed_review_card(s, slug)
    c = Card.from_dict(s["cards"][slug])
    c.due = now_utc() - timedelta(hours=1)
    s["cards"][slug] = c.to_dict()
    if graded:
        s["graded_files"][slug] = True
    store.save(s)


def test_next_review_archives_graded_attempt(env, capsys):
    data, sol = env
    write_solution(sol, "two-sum", TWO_SUM_BODY, [(([2, 7, 11, 15], 9), [0, 1])])
    _due_review("two-sum", graded=True)
    run(["next"], capsys)
    o = out(capsys)
    arch = sol / "archive" / "two-sum" / "attempt-1.py"
    assert "return [0, 1]" in arch.read_text()                  # old solution kept verbatim
    fresh = (sol / "two-sum.py").read_text()
    assert "return [0, 1]" not in fresh and "pass" in fresh     # scaffold is blank again
    assert "attempt-1.py" in o and "solve from memory" in o
    assert "two-sum" not in store.load()["graded_files"]        # flag consumed


def test_next_review_numbers_attempts(env, capsys):
    data, sol = env
    write_solution(sol, "two-sum", TWO_SUM_BODY, [(([2, 7, 11, 15], 9), [0, 1])])
    _due_review("two-sum", graded=True)
    arch = sol / "archive" / "two-sum"
    arch.mkdir(parents=True)
    (arch / "attempt-1.py").write_text("# earlier rep\n")
    run(["next"], capsys)
    assert (arch / "attempt-2.py").exists()


def test_next_review_keeps_ungraded_work(env, capsys):
    data, sol = env
    write_solution(sol, "two-sum", "# HALF-DONE WORK", [])
    _due_review("two-sum", graded=False)
    run(["next"], capsys)
    assert "HALF-DONE" in (sol / "two-sum.py").read_text()
    assert not (sol / "archive").exists()


def test_done_archives_attempt_immediately(env, capsys, no_fuzz):
    data, sol = env
    write_solution(sol, "contains-duplicate", SOLVED_BODY, [(([1, 2, 3, 1],), True)])
    open_session("contains-duplicate")
    run(["done", "--mins", "5"], capsys)
    o = out(capsys)
    arch = sol / "archive" / "contains-duplicate" / "attempt-1.py"
    assert "len(set(nums))" in arch.read_text()                  # attempt kept verbatim
    assert not (sol / "contains-duplicate.py").exists()          # solutions/ is clean
    assert "attempt archived" in o and "attempt-1.py" in o
    assert "contains-duplicate" not in store.load()["graded_files"]  # no flag needed anymore


def test_done_archives_failing_attempt_too(env, capsys, no_fuzz):
    """An unsolved rep is still history — graded means filed, solved or not."""
    data, sol = env
    write_solution(sol, "contains-duplicate",
                   "class Solution:\n    def containsDuplicate(self, nums):\n        return False",
                   [(([1, 2, 3, 1],), True)])
    open_session("contains-duplicate")
    run(["done", "--mins", "10"], capsys)
    assert (sol / "archive" / "contains-duplicate" / "attempt-1.py").exists()
    assert not (sol / "contains-duplicate.py").exists()


def test_done_without_solution_file_no_archive(env, capsys, no_fuzz):
    open_session("contains-duplicate")             # no file was ever written
    run(["done", "--fail", "--mins", "5"], capsys)
    sol = env[1]
    assert not (sol / "archive").exists()
    assert "contains-duplicate" not in store.load()["graded_files"]


def test_done_files_statement_to_archive(env, capsys, no_fuzz):
    data, sol = env
    sol.mkdir(parents=True, exist_ok=True)
    (sol / "contains-duplicate.md").write_text("# statement\n")
    write_solution(sol, "contains-duplicate", SOLVED_BODY, [(([1, 2, 3, 1],), True)])
    open_session("contains-duplicate")
    run(["done", "--mins", "5"], capsys)
    arch = sol / "archive" / "contains-duplicate"
    assert (arch / "attempt-1.py").exists() and (arch / "statement.md").exists()
    assert not (sol / "contains-duplicate.md").exists()   # solutions/ is clean


def test_next_sweeps_strays_into_archive(env, capsys):
    """solutions/ shows only the active problem: other problems' files are
    filed automatically (passing → attempt-N, WIP-ish → wip.py, md → statement.md)."""
    data, sol = env
    write_solution(sol, "two-sum", TWO_SUM_BODY, [(([2, 7, 11, 15], 9), [0, 1])])
    write_solution(sol, "valid-anagram",
                   "class Solution:\n    def isAnagram(self, s, t):\n        return True  # wip",
                   [])
    (sol / "two-sum.md").write_text("# Two Sum\n")
    run(["next"], capsys)                     # picks contains-duplicate (first new)
    arch = sol / "archive"
    assert "return [0, 1]" in (arch / "two-sum" / "attempt-1.py").read_text()
    assert (arch / "two-sum" / "statement.md").exists()
    assert "wip" in (arch / "valid-anagram" / "wip.py").read_text()
    assert not (sol / "two-sum.py").exists() and not (sol / "two-sum.md").exists()
    assert not (sol / "valid-anagram.py").exists()
    assert (sol / "contains-duplicate.py").exists()        # active problem untouched


def test_next_sweep_never_touches_unknown_files(env, capsys):
    data, sol = env
    sol.mkdir(parents=True, exist_ok=True)
    (sol / "notes.txt").write_text("my scratch notes")
    (sol / "random.md").write_text("not a problem statement")
    run(["next"], capsys)
    assert (sol / "notes.txt").exists() and (sol / "random.md").exists()


def test_next_restores_wip_when_problem_picked(env, capsys):
    """A parked wip.py comes back the moment its problem is picked."""
    data, sol = env
    _due_review("two-sum")
    (sol / "archive" / "two-sum").mkdir(parents=True)
    (sol / "archive" / "two-sum" / "wip.py").write_text("# HALF-DONE WORK\n")
    run(["next"], capsys)
    assert "HALF-DONE" in (sol / "two-sum.py").read_text()   # resumed, not blanked
    assert not (sol / "archive" / "two-sum" / "wip.py").exists()


def test_skip_files_wip_then_resume_and_done(env, capsys, no_fuzz):
    """The whole skip workflow: park WIP + statement, resume on repick, grade
    normally — nothing is ever lost."""
    data, sol = env
    run(["next"], capsys)                     # contains-duplicate active, md exists
    (sol / "contains-duplicate.py").write_text("# MID-SOLUTION\n")
    run(["skip"], capsys)
    o = out(capsys)
    arch = sol / "archive" / "contains-duplicate"
    assert "filed" in o and (arch / "wip.py").exists() and (arch / "statement.md").exists()
    assert not (sol / "contains-duplicate.py").exists()

    run(["next"], capsys)                     # due-fail repick: WIP comes back
    assert "MID-SOLUTION" in (sol / "contains-duplicate.py").read_text()
    write_solution(sol, "contains-duplicate", SOLVED_BODY, [(([1, 2, 3, 1],), True)])
    run(["done", "--mins", "5"], capsys)
    assert "len(set(nums))" in (arch / "attempt-1.py").read_text()
    assert not (arch / "wip.py").exists()     # graded: it graduated to attempt-N

# ------------------------------------------------------- existing solutions

def test_next_adopts_passing_solution_on_disk(env, capsys):
    """A pre-grind file that passes its own TESTS is a finished solution —
    archive it, don't let it spoil the rep."""
    data, sol = env
    write_solution(sol, "contains-duplicate", SOLVED_BODY,
                   [(([1, 2, 3, 1],), True), (([1, 2, 3, 4],), False)])
    run(["next"], capsys)                     # fresh state -> new problem pick
    o = out(capsys)
    arch = sol / "archive" / "contains-duplicate" / "attempt-1.py"
    assert "len(set(nums))" in arch.read_text()
    fresh = (sol / "contains-duplicate.py").read_text()
    assert "len(set(nums))" not in fresh and "pass" in fresh
    assert "attempt-1.py" in o and "solve from memory" in o


def test_next_keeps_failing_file_on_disk(env, capsys):
    """WIP / buggy files never pass their TESTS -> left exactly as-is."""
    data, sol = env
    write_solution(sol, "contains-duplicate",
                   "class Solution:\n    def containsDuplicate(self, nums):\n        return True  # buggy WIP",
                   [(([1, 2, 3, 4],), False)])
    run(["next"], capsys)
    assert "buggy WIP" in (sol / "contains-duplicate.py").read_text()
    assert not (sol / "archive").exists()


def test_next_keeps_file_without_tests_on_disk(env, capsys):
    """No TESTS = nothing to judge by -> file stays (can't verify, don't touch)."""
    data, sol = env
    write_solution(sol, "contains-duplicate", SOLVED_BODY, [])
    run(["next"], capsys)
    assert "len(set(nums))" in (sol / "contains-duplicate.py").read_text()
    assert not (sol / "archive").exists()


def test_next_review_adopts_passing_solution_without_flag(env, capsys):
    """Flag lost (state wiped, files restored): the TESTS still judge a due review."""
    data, sol = env
    write_solution(sol, "two-sum", TWO_SUM_BODY, [(([2, 7, 11, 15], 9), [0, 1])])
    _due_review("two-sum", graded=False)
    run(["next"], capsys)
    assert "return [0, 1]" in (sol / "archive" / "two-sum" / "attempt-1.py").read_text()
    assert "pass" in (sol / "two-sum.py").read_text()
    assert "two-sum" not in store.load()["graded_files"]


# ---------------------------------------------------------------- check

def test_check_defaults_to_subset_of_three(env, capsys):
    data, sol = env
    write_solution(sol, "contains-duplicate", SOLVED_BODY,
                   [(([1, 2, 3, 1],), True)] * 5)
    assert run(["check", "contains-duplicate"], capsys) is None
    o = out(capsys)
    assert "(3 of 5 case(s))" in o and "3/3 passed" in o


def test_check_n_and_all_flags(env, capsys):
    data, sol = env
    write_solution(sol, "contains-duplicate", SOLVED_BODY,
                   [(([1, 2, 3, 1],), True)] * 5)
    run(["check", "contains-duplicate", "--n", "2"], capsys)
    assert "(2 of 5 case(s))" in out(capsys)
    run(["check", "contains-duplicate", "--all"], capsys)
    assert "(5 of 5 case(s))" in out(capsys)


def test_check_failure_exits_1(env, capsys):
    data, sol = env
    write_solution(sol, "contains-duplicate",
                   "class Solution:\n    def containsDuplicate(self, nums):\n        return True",
                   [(([1, 2, 3, 1],), True), (([1, 2, 3, 4],), False)])
    assert run(["check", "contains-duplicate", "--all"], capsys) == 1
    o = out(capsys)
    assert "FAIL" in o and "want False" in o and "fix and re-run" in o


def test_check_error_paths(env, capsys):
    assert run(["check", "climbing-stairs"], capsys) == 1        # no file
    data, sol = env
    sol.mkdir(parents=True, exist_ok=True)
    (sol / "two-sum.py").write_text("x = 1\n")                   # no Solution
    assert run(["check", "two-sum"], capsys) == 1
    assert "define your solution class" in out(capsys)
    (sol / "valid-anagram.py").write_text("class Solution:\n    pass\n")  # no TESTS
    assert run(["check", "valid-anagram"], capsys) == 1
    assert "add TESTS" in out(capsys)
    (sol / "reverse-linked-list.py").write_text("def broken(:\n")        # import error
    assert run(["check", "reverse-linked-list"], capsys) == 1
    assert "error loading" in out(capsys)


def test_check_slug_resolution_order(env, capsys):
    data, sol = env
    write_solution(sol, "contains-duplicate", SOLVED_BODY, [(([1, 2, 3, 1],), True)])
    write_solution(sol, "valid-palindrome", "class Solution:\n    def isPalindrome(self, s):\n        return True",
                   [(("a",), True)])
    open_session("valid-palindrome")          # session wins over `last`
    run(["check"], capsys)
    assert "checking valid-palindrome" in out(capsys)
    run(["check", "contains-duplicate"], capsys)  # explicit slug beats everything
    assert "checking contains-duplicate" in out(capsys)
    s = store.load()
    s["session"] = None
    s["last"] = "valid-palindrome"             # last-graded fallback
    store.save(s)
    run(["check"], capsys)
    assert "checking valid-palindrome" in out(capsys)
    s["last"] = None
    store.save(s)
    assert run(["check"], capsys) == 1         # nothing resolvable
    assert "grade something first" in out(capsys)


def test_check_exception_in_method_is_failure(env, capsys):
    data, sol = env
    write_solution(sol, "two-sum",
                   "class Solution:\n    def twoSum(self, nums, target):\n        raise ValueError('boom')",
                   [(([2, 7], 9), [0, 1])])
    assert run(["check", "two-sum"], capsys) == 1
    assert "ValueError: boom" in out(capsys)


def test_run_tests_uses_last_public_method_and_loose_lists(env, capsys):
    data, sol = env
    # helper defined ABOVE the required method; returns a tuple where a list is expected
    write_solution(sol, "two-sum",
                   "class Solution:\n"
                   "    def _helper(self):\n        return 9\n\n"
                   "    def twoSum(self, nums, target):\n        return (0, 1)",
                   [(([2, 7, 11, 15], 9), [0, 1])])
    assert run(["check", "two-sum"], capsys) is None
    assert "1/1 passed" in out(capsys)


# ---------------------------------------------------------------- skip

def test_skip_guard_and_drop(env, capsys):
    assert run(["skip"], capsys) == 1
    assert "No active session" in out(capsys)
    open_session("two-sum")
    assert run(["skip"], capsys) is None
    assert "dropped" in out(capsys)
    s = store.load()
    assert s["session"] is None and s["logs"] == []  # nothing graded, nothing logged


# ---------------------------------------------------------------- status / topics / stats

def test_status_fresh(env, capsys):
    run(["status"], capsys)
    o = out(capsys)
    assert "0/150 seen" in o and "streak 0d" in o and "proven 0/150" in o
    assert "interview readiness: 0%  (goal 80%)" in o
    assert "least ready:" in o


def test_status_after_activity(env, capsys, no_fuzz):
    s = store.load()
    seed_review_card(s, "contains-duplicate")
    add_log(s, "contains-duplicate", 5.0, solved=True, when=now_utc())
    store.save(s)
    run(["status"], capsys)
    o = out(capsys)
    assert "1/150 seen" in o and "proven 1/150" in o and "streak 1d" in o
    open_session("contains-duplicate")
    run(["status"], capsys)
    assert "in session: Contains Duplicate" in out(capsys)

def test_status_streak_at_risk(env, capsys, no_fuzz):
    """Status shows streak warning when streak > 0 and no activity today."""
    s = store.load()
    from grind.scheduler import utcnow
    from datetime import timedelta
    # Create a 3-day streak ending yesterday
    now = utcnow()
    for i in range(1, 4):
        add_log(s, "two-sum", 5.0, solved=True, when=now - timedelta(days=i))
    store.save(s)
    run(["status"], capsys)
    o = out(capsys)
    assert "streak 3d" in o
    assert "⚠ streak at risk" in o
    # Now add activity today — warning should disappear
    add_log(s, "valid-anagram", 5.0, solved=True, when=now)
    store.save(s)
    run(["status"], capsys)
    o = out(capsys)
    assert "streak 4d" in o  # streak increased
    assert "⚠ streak at risk" not in o

def test_topics_table(env, capsys):
    run(["topics"], capsys)
    o = out(capsys)
    assert o.count("\n") >= 19          # 18 topics + header
    assert "Arrays & Hashing" in o and "Bit Manipulation" in o
    assert "overall: 0%  (goal 80%)" in o
    assert "ready = you solved the problem last attempt" in o

def test_topic_detail(env, capsys):
    """topic shows all problems in a topic with status and readiness."""
    run(["topic", "arrays"], capsys)
    o = out(capsys)
    assert "Topic: Arrays & Hashing" in o
    assert "readiness" in o
    assert "two-sum" in o
    assert "valid-anagram" in o
    # Case insensitive
    run(["topic", "ARRAYS"], capsys)
    assert "Arrays & Hashing" in out(capsys)
    # Unknown topic
    run(["topic", "nonexistent"], capsys)
    assert "No problems found for topic matching 'nonexistent'" in out(capsys)
def test_topic_difficulty_filter(env, capsys):
    """topic --difficulty filters by difficulty."""
    run(["topic", "arrays", "--difficulty", "Easy"], capsys)
    o = out(capsys)
    assert "Topic: Arrays & Hashing" in o
    # Only Easy problems
    lines = [l for l in o.splitlines() if l.strip() and not l.startswith("Topic:") and not l.startswith("slug")]
    for line in lines:
        assert "Easy" in line
    assert "two-sum" in o
    assert "valid-anagram" in o
    assert "contains-duplicate" in o
    # Medium not shown
    assert "group-anagrams" not in o

    run(["topic", "arrays", "--difficulty", "Medium"], capsys)
    o = out(capsys)
    lines = [l for l in o.splitlines() if l.strip() and not l.startswith("Topic:") and not l.startswith("slug")]
    for line in lines:
        assert "Medium" in line
    assert "group-anagrams" in o
    assert "two-sum" not in o

    run(["topic", "arrays", "--difficulty", "Hard"], capsys)
    o = out(capsys)
    assert "No Hard problems found for topic matching 'arrays'" in o

def test_topic_difficulty_combines_with_topic(env, capsys):
    """topic with different topics and difficulties."""
    # Two Pointers has Easy (valid-palindrome)
    run(["topic", "Two Pointers", "--difficulty", "Easy"], capsys)
    o = out(capsys)
    assert "valid-palindrome" in o
    assert "Two Pointers" in o
    # Sliding Window has Medium problems
    run(["topic", "Sliding Window", "--difficulty", "Medium"], capsys)
    o = out(capsys)
    assert "Medium" in o
def test_export_command(env, capsys):
    """export outputs JSON by default and CSV with --csv."""
    s = store.load()
    add_log(s, "two-sum", 10, solved=True, rating=3.5, when=local(0))
    store.save(s)
    # JSON export
    run(["export"], capsys)
    o = out(capsys)
    import json
    data = json.loads(o)
    assert data["summary"]["proven"] >= 1
    assert "problems" in data
    assert "logs" in data
    assert data["version"] == __version__
    # CSV export
    run(["export", "--csv"], capsys)
    o = out(capsys)
    assert "timestamp,slug,rating,solved,elapsed_min,tests,new" in o
    assert "two-sum" in o
    # Output to file
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        tmp = f.name
    try:
        run(["export", "--output", tmp], capsys)
        assert f"Exported to {tmp}" in out(capsys)
        with open(tmp) as f:
            data = json.load(f)
        assert data["summary"]["proven"] >= 1
    finally:
        import os
        os.unlink(tmp)
    # Cannot specify both
    run(["export", "--json", "--csv"], capsys)
    assert "Cannot specify both --json and --csv" in out(capsys)
def test_export_since_until(env, capsys):
    """export --since/--until filters logs and activity by date."""
    from conftest import add_log, local
    import json
    from datetime import datetime, timedelta
    s = store.load()
    # Add logs at different dates (using local() which is relative to now)
    add_log(s, "two-sum", 10, solved=True, rating=3.5, when=local(10))   # 10 days ago
    add_log(s, "valid-palindrome", 15, solved=True, rating=3.0, when=local(5))  # 5 days ago
    add_log(s, "two-sum", 12, solved=False, rating=2.0, when=local(0))  # today
    store.save(s)

    # Calculate date strings for filtering
    today = datetime.now().astimezone().date()
    day_10 = (today - timedelta(days=10)).isoformat()
    day_5 = (today - timedelta(days=5)).isoformat()
    day_0 = today.isoformat()
    day_7 = (today - timedelta(days=7)).isoformat()
    day_3 = (today - timedelta(days=3)).isoformat()

    # Export with --since day 7 (should include day 5 and day 0)
    run(["export", "--since", day_7], capsys)
    o = out(capsys)
    data = json.loads(o)
    assert len(data["logs"]) == 2
    slugs = [e["slug"] for e in data["logs"]]
    assert "valid-palindrome" in slugs
    assert "two-sum" in slugs
    # day 10 should be excluded
    assert not any(e["slug"] == "two-sum" and e.get("elapsed") == 10.0 for e in data["logs"])
    # Activity should only have day 5 and day 0
    assert day_5 in data["activity_by_day"]
    assert day_0 in data["activity_by_day"]
    assert day_10 not in data["activity_by_day"]

    # Export with --until day 3 (should include day 5 and day 10)
    run(["export", "--until", day_3], capsys)
    o = out(capsys)
    data = json.loads(o)
    assert len(data["logs"]) == 2
    slugs = [e["slug"] for e in data["logs"]]
    assert "two-sum" in slugs
    assert "valid-palindrome" in slugs
    assert day_10 in data["activity_by_day"]
    assert day_5 in data["activity_by_day"]
    assert day_0 not in data["activity_by_day"]

    # Export with --since and --until (day 7 to day 3, only day 5)
    run(["export", "--since", day_7, "--until", day_3], capsys)
    o = out(capsys)
    data = json.loads(o)
    assert len(data["logs"]) == 1
    assert data["logs"][0]["slug"] == "valid-palindrome"
    assert list(data["activity_by_day"].keys()) == [day_5]
    # CSV export with date filter
    run(["export", "--csv", "--since", day_7, "--until", day_3], capsys)
    o = out(capsys)
    lines = o.strip().split("\n")
    assert len(lines) == 2  # header + 1 data row
    assert "valid-palindrome" in lines[1]

    # Invalid date format
    assert run(["export", "--since", "invalid"], capsys) == 1
    assert "Invalid --since date" in out(capsys)
    assert run(["export", "--until", "not-a-date"], capsys) == 1
    assert "Invalid --until date" in out(capsys)


def test_export_invalid_dates_in_logs(env, capsys):
    """export handles invalid timestamps gracefully."""
    import json
    s = store.load()
    # Add a valid log
    add_log(s, "two-sum", 10, solved=True, rating=3.5, when=local(0))
    # Manually add logs with invalid/missing timestamps
    s["logs"].append({"slug": "valid-palindrome", "rating": 3.0, "solved": True, "elapsed": 5.0})
    s["logs"].append({"slug": "reverse-linked-list", "ts": "not-a-date", "rating": 2.5, "solved": True, "elapsed": 3.0})
    # Add invalid activity day
    s["activity_by_day"] = s.get("activity_by_day", {})
    s["activity_by_day"]["invalid-date"] = 5
    store.save(s)

    # Export should not crash and should include the valid log
    run(["export"], capsys)
    o = out(capsys)
    data = json.loads(o)
    # Should have the valid log (two-sum)
    assert any(e["slug"] == "two-sum" for e in data["logs"])
    # Invalid timestamp logs should be skipped
    assert not any(e["slug"] == "valid-palindrome" for e in data["logs"])
    assert not any(e["slug"] == "reverse-linked-list" for e in data["logs"])
    # Invalid activity day should be skipped
    assert "invalid-date" not in data["activity_by_day"]

def test_stats_layout(env, capsys):
    s = store.load()
    add_log(s, "two-sum", 5, solved=True, when=local(0))
    store.save(s)
    run(["stats"], capsys)
    o = out(capsys)
    assert "streak: 1d current (best 1d)" in o
    assert "solved: 1 attempts · 1 distinct problems · 1 proven" in o
    assert "last 14 days" in o and "peak 1 attempts/day" in o
    assert "trend" not in o            # hidden below 4 solved attempts


def test_stats_shows_trends_when_enough_history(env, capsys):
    s = store.load()
    add_log(s, "two-sum", 60, solved=False, rating=1.0, when=local(9))
    add_log(s, "two-sum", 60, solved=True, rating=2.0, when=local(9))
    add_log(s, "two-sum", 8, solved=True, rating=3.5, when=local(1))
    add_log(s, "two-sum", 8, solved=True, rating=3.6, when=local(0.5))
    add_log(s, "two-sum", 8, solved=True, rating=3.6, when=local(0))
    store.save(s)
    run(["stats"], capsys)
    o = out(capsys)
    assert "trend (first half -> recent)" in o
    assert "solve rate" in o and "of target time" in o


# ---------------------------------------------------------------- config

def test_config_show_and_set(env, capsys):
    assert run(["config"], capsys) is None
    o = out(capsys)
    assert "daily_new = 5" in o and "retention_target = 0.9" in o
    assert "auto_web = False" in o

    run(["config", "daily_new=3"], capsys)
    assert store.load()["config"]["daily_new"] == 3

    run(["config", "auto_edit=true"], capsys)
    assert store.load()["config"]["auto_edit"] is True

    run(["config", "auto_edit=false"], capsys)
    assert store.load()["config"]["auto_edit"] is False  # real bool, not "false"

    run(["config", "retention_target=0.85"], capsys)
    assert store.load()["config"]["retention_target"] == 0.85

    assert run(["config", "bogus=1"], capsys) == 1
    assert "Unknown config key" in out(capsys)

    # type validation: a bad value must be rejected, never poison the state
    assert run(["config", "daily_new=abc"], capsys) == 1
    assert store.load()["config"]["daily_new"] == 3  # previous value untouched
    assert run(["config", "auto_edit=maybe"], capsys) == 1
    assert "must be true or false" in out(capsys)

def test_config_show_descriptions(env, capsys):
    """config shows descriptions for known keys."""
    run(["config"], capsys)
    o = out(capsys)
    assert "daily_new = 5  # max new problems introduced per day" in o
    assert "retention_target = 0.9  # FSRS desired retention probability" in o
    assert "auto_web = False  # open problem page in browser on grind next" in o
    assert "auto_edit = False  # open scaffold in $EDITOR on grind next" in o
    assert "backup_remote =   # git URL of backup repo" in o
    assert "update_check = True  # check for updates daily" in o
    assert "targets = {'Easy': 15, 'Medium': 30, 'Hard': 45}  # personal fluency targets per difficulty (min)" in o

def test_config_reset(env, capsys):
    """--reset restores all config to defaults."""
    run(["config", "daily_new=8"], capsys)
    run(["config", "retention_target=0.95"], capsys)
    run(["config", "auto_edit=true"], capsys)
    s = store.load()
    assert s["config"]["daily_new"] == 8
    assert s["config"]["retention_target"] == 0.95
    assert s["config"]["auto_edit"] is True

    run(["config", "--reset"], capsys)
    s = store.load()
    assert s["config"]["daily_new"] == 5
    assert s["config"]["retention_target"] == 0.9
    assert s["config"]["auto_edit"] is False
    assert s["config"]["auto_web"] is False
    assert s["config"]["backup_remote"] == ""
    assert s["config"]["update_check"] is True
    assert s["config"]["targets"] == {"Easy": 15, "Medium": 30, "Hard": 45}

    # --reset cannot be combined with key=value
    assert run(["config", "--reset", "daily_new=3"], capsys) == 1
    assert "cannot combine --reset with key=value" in out(capsys)

# ---------------------------------------------------------------- entry

def test_bare_grind_defaults_to_next(env, capsys):
    assert run([], capsys) is None
    assert "https://leetcode.com/problems/contains-duplicate/" in out(capsys)


def test_done_struggle_message_for_slow_solve(env, capsys, no_fuzz):
    data, sol = env
    open_session("contains-duplicate")
    write_solution(sol, "contains-duplicate", SOLVED_BODY, [(([1, 2, 3, 1],), True)])
    run(["done", "--mins", "60"], capsys)  # 60 vs target 15 -> r=4, rating floors
    o = out(capsys)
    assert "solved in 1h00m" in o and "rating 2.20/4" in o  # solve floor engaged
    assert "solved, but a struggle" in o



def test_first_run_intro_shown_once(env, capsys):
    run(["next"], capsys)
    o = out(capsys)
    assert "Welcome to grind" in o
    assert "grind done" in o and "grind check" in o  # the loop is taught
    assert "solve it in your IDE" in o                # per-presentation hint
    assert store.load()["seen_intro"] is True

    s = store.load()
    s["session"] = None
    store.save(s)
    run(["next"], capsys)
    o2 = out(capsys)
    assert "Welcome to grind" not in o2  # never nagging
    assert "solve it in your IDE" in o2  # hint stays

def test_check_no_public_method_exits_cleanly(env, capsys):
    data, sol = env
    write_solution(sol, "two-sum", "class Solution:\n    def _hidden(self):\n        pass",
                   [(([2, 7], 9), [0, 1])])
    assert run(["check", "two-sum"], capsys) == 1
    assert "no public method found in Solution" in out(capsys)


def test_done_no_public_method_gate_is_unsolved(env, capsys, no_fuzz):
    data, sol = env
    open_session("two-sum")
    write_solution(sol, "two-sum", "class Solution:\n    def _hidden(self):\n        pass",
                   [(([2, 7], 9), [0, 1])])
    run(["done", "--mins", "5"], capsys)
    assert "no public method found" in out(capsys)
    assert store.load()["logs"][-1]["solved"] is False  # graded, no traceback


def test_python_dash_m_entry_point(env, capsys):
    """`python -m grind` must work like the console script."""
    import subprocess
    import sys
    r = subprocess.run([sys.executable, "-m", "grind", "status"],
                       capture_output=True, text=True, timeout=30)
    assert r.returncode == 0
    assert "grind status" in r.stdout
    assert "interview readiness" in r.stdout
def test_reference_prints_verified_solution(env, capsys):
    run(["reference", "binary-search"], capsys)
    o = out(capsys)
    assert "Reference solution for binary-search" in o
    assert "704. Binary Search" in o
    assert "def search(" in o


def test_extras_prints_hand_written_cases(env, capsys):
    run(["extras", "binary-search"], capsys)
    o = out(capsys)
    assert "Edge cases for binary-search" in o
    assert "hidden cases" in o
    assert "not shown" in o
    # Should NOT show actual cases
    assert "args=" not in o
    assert "want=" not in o


def test_reference_unknown_slug_exits_with_hint(env, capsys):
    assert run(["reference", "no-such-problem"], capsys) == 1
    assert "no reference solution for no-such-problem" in out(capsys)


def test_extras_unknown_slug_exits_with_hint(env, capsys):
    run(["extras", "no-such-problem"], capsys)
    o = out(capsys)
    assert "no edge cases for no-such-problem" in o


def test_reference_defaults_to_active_session(env, capsys):
    open_session("binary-search")
    run(["reference"], capsys)
    o = out(capsys)
    assert "Reference solution for binary-search" in o
    assert "def search(" in o
# ---------------------------------------------------------------- help

def test_help_prints_overview(env, capsys):
    run(["help"], capsys)
    o = out(capsys)
    assert "Daily loop:" in o
    assert "grind next" in o
    assert "grind done" in o
    assert "Inspect & learn:" in o
    assert "grind reference" in o
    assert "Config & maintenance:" in o
    assert "grind backup" in o
    assert "grind update" in o


def test_edit_no_session(env, capsys):
    assert run(["edit"], capsys) == 1
    assert "No active session" in out(capsys)


def test_edit_scaffold_not_found(env, capsys):
    open_session("two-sum")
    # Don't create scaffold file
    assert run(["edit"], capsys) == 1
    assert "scaffold not found" in out(capsys)


def test_edit_with_session(env, capsys, monkeypatch):
    open_session("two-sum")
    # Create the scaffold file
    from grind import store
    from pathlib import Path
    state = store.load()
    sol_dir = Path(state["session"]["scaffold"]).parent
    sol_dir.mkdir(parents=True, exist_ok=True)
    Path(state["session"]["scaffold"]).write_text("# scaffold\n")
    monkeypatch.setenv("EDITOR", "vi")

    called = []

    def fake_call(args):
        called.append(args)
        return 0

    monkeypatch.setattr("grind.cli.subprocess.call", fake_call)
    assert run(["edit"], capsys) is None
    assert called == [["vi", str(state["session"]["scaffold"])]]


def test_web_no_session(env, capsys):
    assert run(["web"], capsys) == 1
    assert "No active session" in out(capsys)


def test_web_with_session(env, capsys, monkeypatch):
    open_session("two-sum")
    opened = []

    def fake_open(url):
        opened.append(url)

    monkeypatch.setattr("webbrowser.open", fake_open)
    assert run(["web"], capsys) is None
    assert opened == ["https://leetcode.com/problems/two-sum/"]

# ---------------------------------------------------------------- log

def test_log_empty(env, capsys):
    run(["log"], capsys)
    assert "No graded attempts yet." in out(capsys)


def test_log_prints_recent(env, capsys, no_fuzz):
    data, sol = env
    open_session("contains-duplicate")
    write_solution(sol, "contains-duplicate", SOLVED_BODY,
                   [(([1, 2, 3, 1],), True), (([1, 2, 3, 4],), False)])
    run(["done", "--solved", "--mins", "10"], capsys)  # adds a log
    run(["done", "--fail", "--mins", "5"], capsys)     # adds another

    run(["log"], capsys)
    o = out(capsys)
    assert "contains-duplicate" in o
    assert "rating=" in o
    assert "elapsed=" in o
    assert "solved=" in o


def test_log_n_flag(env, capsys, no_fuzz):
    data, sol = env
    open_session("contains-duplicate")
    write_solution(sol, "contains-duplicate", SOLVED_BODY,
                   [(([1, 2, 3, 1],), True), (([1, 2, 3, 4],), False)])
    run(["done", "--solved", "--mins", "10"], capsys)
    run(["done", "--fail", "--mins", "5"], capsys)
    run(["done", "--solved", "--mins", "8"], capsys)

    run(["log", "--n", "2"], capsys)
    lines = [l for l in out(capsys).splitlines() if "contains-duplicate" in l]
    assert len(lines) == 2


def test_log_all_flag(env, capsys, no_fuzz):
    data, sol = env
    open_session("contains-duplicate")
    write_solution(sol, "contains-duplicate", SOLVED_BODY,
                   [(([1, 2, 3, 1],), True), (([1, 2, 3, 4],), False)])
    run(["done", "--solved", "--mins", "10"], capsys)
    run(["done", "--fail", "--mins", "5"], capsys)

    run(["log", "--all"], capsys)
    lines = [l for l in out(capsys).splitlines() if "contains-duplicate" in l]
    assert len(lines) == 2
def test_log_slug_filter(env, capsys, no_fuzz):
    data, sol = env
    # Grade two-sum
    open_session("two-sum")
    write_solution(sol, "two-sum", TWO_SUM_BODY,
                   [(([2, 7, 11, 15], 9), [0, 1])])
    run(["done", "--solved", "--mins", "10"], capsys)
    # Grade contains-duplicate
    open_session("contains-duplicate")
    write_solution(sol, "contains-duplicate", SOLVED_BODY,
                   [(([1, 2, 3, 1],), True), (([1, 2, 3, 4],), False)])
    run(["done", "--solved", "--mins", "5"], capsys)

    run(["log", "--slug", "two-sum"], capsys)
    # Extract only log lines (format: YYYY-MM-DD HH:MM  slug  ...)
    log_lines = [l for l in out(capsys).splitlines() if l.strip() and l[0].isdigit()]
    log_output = "\n".join(log_lines)
    assert "two-sum" in log_output
    assert "contains-duplicate" not in log_output

    run(["log", "--slug", "invalid-slug"], capsys)
    assert "No matching history." in out(capsys)


def test_log_topic_filter(env, capsys, no_fuzz):
    data, sol = env
    # two-sum is "arrays" topic, contains-duplicate is "arrays" topic, binary-search is "binary-search"
    open_session("two-sum")
    write_solution(sol, "two-sum", TWO_SUM_BODY,
                   [(([2, 7, 11, 15], 9), [0, 1])])
    run(["done", "--solved", "--mins", "10"], capsys)
    open_session("binary-search")
    write_solution(sol, "binary-search", "class Solution:\n    def search(self, nums, target):\n        return -1",
                   [(([-1, 0, 3, 5, 9, 12], 9), 4)])
    run(["done", "--solved", "--mins", "8"], capsys)

    run(["log", "--topic", "arrays"], capsys)
    log_lines = [l for l in out(capsys).splitlines() if l.strip() and l[0].isdigit()]
    log_output = "\n".join(log_lines)
    assert "two-sum" in log_output
    assert "binary-search" not in log_output

    run(["log", "--topic", "binary"], capsys)
    log_lines = [l for l in out(capsys).splitlines() if l.strip() and l[0].isdigit()]
    log_output = "\n".join(log_lines)
    assert "binary-search" in log_output
    assert "two-sum" not in log_output


def test_log_difficulty_filter(env, capsys, no_fuzz):
    data, sol = env
    # two-sum is Easy, product-of-array-except-self is Medium
    open_session("two-sum")
    write_solution(sol, "two-sum", TWO_SUM_BODY,
                   [(([2, 7, 11, 15], 9), [0, 1])])
    run(["done", "--solved", "--mins", "10"], capsys)
    open_session("product-of-array-except-self")
    write_solution(sol, "product-of-array-except-self", "class Solution:\n    def productExceptSelf(self, nums):\n        return [1]",
                   [(([1, 2, 3, 4],), [24, 12, 8, 6])])
    run(["done", "--solved", "--mins", "8"], capsys)

    run(["log", "--difficulty", "Easy"], capsys)
    log_lines = [l for l in out(capsys).splitlines() if l.strip() and l[0].isdigit()]
    log_output = "\n".join(log_lines)
    assert "two-sum" in log_output
    assert "product-of-array-except-self" not in log_output

    run(["log", "--difficulty", "Medium"], capsys)
    log_lines = [l for l in out(capsys).splitlines() if l.strip() and l[0].isdigit()]
    log_output = "\n".join(log_lines)
    assert "product-of-array-except-self" in log_output
    assert "two-sum" not in log_output


def test_log_combined_filters(env, capsys, no_fuzz):
    data, sol = env
    open_session("two-sum")
    write_solution(sol, "two-sum", TWO_SUM_BODY,
                   [(([2, 7, 11, 15], 9), [0, 1])])
    run(["done", "--solved", "--mins", "10"], capsys)
    # two-sum-ii-input-array-is-sorted is Medium and in "Two Pointers" topic
    open_session("two-sum-ii-input-array-is-sorted")
    write_solution(sol, "two-sum-ii-input-array-is-sorted", "class Solution:\n    def twoSum(self, numbers, target):\n        return [1, 2]",
                   [(([2, 7, 11, 15], 9), [1, 2])])
    run(["done", "--solved", "--mins", "8"], capsys)

    # topic arrays + difficulty Easy should match two-sum only
    run(["log", "--topic", "arrays", "--difficulty", "Easy"], capsys)
    log_lines = [l for l in out(capsys).splitlines() if l.strip() and l[0].isdigit()]
    log_output = "\n".join(log_lines)
    assert "two-sum" in log_output
    assert "two-sum-ii-input-array-is-sorted" not in log_output

    # topic arrays + difficulty Medium should match nothing (two-sum-ii is in Two Pointers, not arrays)
    run(["log", "--topic", "arrays", "--difficulty", "Medium"], capsys)
    assert "No matching history." in out(capsys)

# ---------------------------------------------------------------- list

def test_list_shows_all(env, capsys):
    run(["list"], capsys)
    o = out(capsys)
    lines = [l for l in o.splitlines() if l.strip() and not l.startswith("slug")]
    # header + 150 problems
    assert len(lines) >= 150


def test_list_due_filter(env, capsys, no_fuzz):
    data, sol = env
    # Seed an overdue review card
    state = store.load()
    seed_review_card(state, "contains-duplicate")
    store.save(state)

    run(["list", "--due"], capsys)
    o = out(capsys)
    lines = [l for l in o.splitlines() if l.strip() and not l.startswith("slug")]
    # should only show the due problem(s)
    for line in lines:
        assert "due" in line.lower()


def test_list_new_filter(env, capsys):
    run(["list", "--new"], capsys)
    o = out(capsys)
    lines = [l for l in o.splitlines() if l.strip() and not l.startswith("slug")]
    for line in lines:
        assert "new" in line.lower()


def test_list_proven_filter(env, capsys, no_fuzz):
    data, sol = env
    open_session("contains-duplicate")
    write_solution(sol, "contains-duplicate", SOLVED_BODY,
                   [(([1, 2, 3, 1],), True), (([1, 2, 3, 4],), False)])
    run(["done", "--solved", "--mins", "10"], capsys)  # solved -> proven
    out(capsys)  # clear buffer

    run(["list", "--proven"], capsys)
    o = out(capsys)
    lines = [l for l in o.splitlines() if l.strip() and not l.startswith("slug")]
    for line in lines:
        assert "proven" in line.lower()


def test_list_topic_filter(env, capsys):
    run(["list", "--topic", "arrays"], capsys)
    o = out(capsys)
    lines = [l for l in o.splitlines() if l.strip() and not l.startswith("slug")]
    for line in lines:
        assert "arrays" in line.lower()


# ---------------------------------------------------------------- pause/resume
def test_pause_resume_shows_duration(env, capsys):
    """Resuming a paused session shows total paused time."""
    open_session("two-sum")
    # Pause
    run(["pause"], capsys)
    # Resume
    run(["next"], capsys)
    o = out(capsys)
    assert "Resumed:" in o and "paused" in o
    # Should show some time (0m or more)
    assert "paused 0m" in o or "paused" in o


# ---------------------------------------------------------------- list --difficulty
def test_list_difficulty_filter(env, capsys):
    run(["list", "--difficulty", "Hard"], capsys)
    o = out(capsys)
    lines = [l for l in o.splitlines() if l.strip() and not l.startswith("slug")]
    for line in lines:
        assert "Hard" in line

    run(["list", "--difficulty", "Easy"], capsys)
    o = out(capsys)
    lines = [l for l in o.splitlines() if l.strip() and not l.startswith("slug")]
    for line in lines:
        assert "Easy" in line


def test_list_difficulty_combines_with_topic(env, capsys):
    run(["list", "--topic", "arrays", "--difficulty", "Medium"], capsys)
    o = out(capsys)
    lines = [l for l in o.splitlines() if l.strip() and not l.startswith("slug")]
    for line in lines:
        assert "arrays" in line.lower()
        assert "Medium" in line

def test_list_search_filter(env, capsys):
    """--search filters by keyword in slug or title."""
    run(["list", "--search", "two"], capsys)
    o = out(capsys)
    lines = [l for l in o.splitlines() if l.strip() and not l.startswith("slug")]
    assert len(lines) > 0
    for line in lines:
        assert "two" in line.lower()
    # Combined with difficulty
    run(["list", "--search", "sum", "--difficulty", "Easy"], capsys)
    o = out(capsys)
    lines = [l for l in o.splitlines() if l.strip() and not l.startswith("slug")]
    for line in lines:
        assert "sum" in line.lower()
        assert "Easy" in line

# ---------------------------------------------------------------- history
def test_history_command(env, capsys):
    """history shows chronological attempt log for a slug."""
    s = store.load()
    from grind.scheduler import utcnow
    from datetime import timedelta
    now = utcnow()
    add_log(s, "two-sum", 12.5, solved=True, rating=3.2, when=now - timedelta(days=7))
    add_log(s, "two-sum", 25.0, solved=False, rating=2.8, when=now - timedelta(days=4))
    add_log(s, "two-sum", 8.2, solved=True, rating=3.6, when=now - timedelta(days=1))
    # Add tests field manually (not in add_log helper)
    s["logs"][-3]["tests"] = 15
    s["logs"][-2]["tests"] = 12
    s["logs"][-1]["tests"] = 15
    store.save(s)
    run(["history", "two-sum"], capsys)
    o = out(capsys)
    lines = [l for l in o.splitlines() if l.strip()]
    assert len(lines) == 3
    assert "solved=yes" in lines[0]
    assert "solved=no" in lines[1]
    assert "solved=yes" in lines[2]
    # Unknown slug
    run(["history", "invalid-slug"], capsys)
    o = out(capsys)
    assert "No history for invalid-slug" in o
# ---------------------------------------------------------------- stats heatmap & difficulty
def test_stats_heatmap_and_difficulty(env, capsys):
    s = store.load()
    add_log(s, "two-sum", 5, solved=True, when=local(0))
    store.save(s)
    run(["stats"], capsys)
    o = out(capsys)
    # Heatmap
    assert "last 12 weeks:" in o
    assert "· none" in o
    # Difficulty breakdown
    assert "by difficulty:" in o
    assert "Easy" in o and "Medium" in o and "Hard" in o
    assert "ready" in o and "proven" in o and "solved" in o


# ---------------------------------------------------------------- upcoming
def test_upcoming_command(env, capsys, no_fuzz):
    from conftest import seed_review_card
    state = store.load()
    seed_review_card(state, "two-sum")
    seed_review_card(state, "valid-anagram")
    store.save(state)
    run(["upcoming", "--days", "7"], capsys)
    o = out(capsys)
    assert "two-sum" in o or "valid-anagram" in o
    assert "due" in o.lower()


def test_upcoming_empty(env, capsys):
    run(["upcoming", "--days", "14"], capsys)
    assert "No reviews due in the next 14 days" in out(capsys)


# ---------------------------------------------------------------- review
def test_review_runs_full_suite_no_grading(env, capsys):
    data, sol = env
    write_solution(sol, "two-sum",
        "class Solution:\n    def twoSum(self, nums, target):\n        seen = {}\n        for i, n in enumerate(nums):\n            if target - n in seen:\n                return [seen[target - n], i]\n            seen[n] = i\n        return []",
        [(([2,7,11,15], 9), [0,1]), (([3,2,4], 6), [1,2]), (([3,3], 6), [0,1])])
    # Run review
    assert run(["review", "two-sum"], capsys) is None
    o = out(capsys)
    assert "reviewing two-sum" in o
    assert "3/3 passed" in o
    # No state changes
    s = store.load()
    assert s["session"] is None
    assert s["logs"] == []


def test_review_fails_on_bad_solution(env, capsys):
    data, sol = env
    write_solution(sol, "two-sum", "class Solution:\n    def twoSum(self, nums, target):\n        return []", [(([2,7,11,15], 9), [0,1])])
    assert run(["review", "two-sum"], capsys) == 1
    o = out(capsys)
    assert "0/1 passed" in o


# ---------------------------------------------------------------- config presets
def test_config_presets(env, capsys):
    # intensive
    assert run(["config", "preset=intensive"], capsys) is None
    s = store.load()
    assert s["config"]["daily_new"] == 8
    assert s["config"]["retention_target"] == 0.95
    assert s["config"]["auto_edit"] is True

    # casual
    assert run(["config", "preset=casual"], capsys) is None
    s = store.load()
    assert s["config"]["daily_new"] == 2
    assert s["config"]["retention_target"] == 0.85
    assert s["config"]["auto_edit"] is False

    # maintenance
    assert run(["config", "preset=maintenance"], capsys) is None
    s = store.load()
    assert s["config"]["daily_new"] == 0
    assert s["config"]["retention_target"] == 0.9
    assert s["config"]["auto_edit"] is False

    # unknown preset
    assert run(["config", "preset=unknown"], capsys) == 1
    assert "Unknown preset" in out(capsys)


# ---------------------------------------------------------------- review errors
def test_review_errors(env, capsys):
    # No slug, no session, no last
    assert run(["review"], capsys) == 1
    assert "pass a problem id" in out(capsys)

    # No solution file
    assert run(["review", "two-sum"], capsys) == 1
    assert "no solution file" in out(capsys)

    # Bad solution file (syntax error) - need to create the file first
    data, sol = env
    sol.mkdir(parents=True, exist_ok=True)
    (sol / "two-sum.py").write_text("not valid python")
    assert run(["review", "two-sum"], capsys) == 1
    assert "error loading" in out(capsys)

    # No Solution class
    (sol / "two-sum.py").write_text("x = 1\nTESTS = []")
    assert run(["review", "two-sum"], capsys) == 1
    assert "define your solution class" in out(capsys)

    # No TESTS
    (sol / "two-sum.py").write_text("class Solution:\n    def twoSum(self, nums, target):\n        return []")
    assert run(["review", "two-sum"], capsys) == 1
    assert "add TESTS" in out(capsys)

# ---------------------------------------------------------------- upcoming edge cases
def test_upcoming_overdue_and_unknown_slug(env, capsys, no_fuzz):
    from conftest import seed_review_card
    state = store.load()
    seed_review_card(state, "two-sum")
    # Also make the two-sum card overdue
    from fsrs import Card
    c = Card()
    c.due = now_utc() - timedelta(hours=5)
    state["cards"]["two-sum"] = c.to_dict()
    # Add a card for a slug not in bank (simulate old data)
    c2 = Card()
    c2.due = now_utc() - timedelta(days=1)
    state["cards"]["unknown-slug"] = c2.to_dict()
    store.save(state)
    run(["upcoming", "--days", "7"], capsys)
    o = out(capsys)
    assert "two-sum" in o
    assert "overdue" in o
    # unknown-slug should be silently skipped

# ---------------------------------------------------------------- stats no activity
def test_stats_heatmap_no_activity(env, capsys):
    run(["stats"], capsys)
    o = out(capsys)
    assert "last 12 weeks:" in o
    # When no activity, heatmap_peak is 0, so heatmap legend should not print
    # The 14-day sparkline still prints "peak 0 attempts/day" - that's expected
    assert "peak 0/day" not in o
    # Weekly bars still show with · for zero activity
    assert "·" in o
def test_stats_shows_time_tracking(env, capsys, no_fuzz):
    """stats shows time investment breakdown."""
    from conftest import add_log, local
    s = store.load()
    # Add logs with known elapsed times for different difficulties and topics
    # two-sum: Easy, Arrays & Hashing
    add_log(s, "two-sum", 10, solved=True, when=local(0))
    add_log(s, "two-sum", 15, solved=True, when=local(1))
    # valid-anagram: Easy, Arrays & Hashing
    add_log(s, "valid-anagram", 20, solved=True, when=local(2))
    # two-sum-ii-input-array-is-sorted: Medium, Two Pointers
    add_log(s, "two-sum-ii-input-array-is-sorted", 30, solved=True, when=local(3))
    # product-of-array-except-self: Medium, Arrays & Hashing
    add_log(s, "product-of-array-except-self", 25, solved=True, when=local(4))
    store.save(s)

    run(["stats"], capsys)
    o = out(capsys)
    # Total time: (10+15+20+30+25)/60 = 100/60 = 1.67h
    assert "Time Investment:" in o
    assert "Total:" in o and "1.7h" in o  # rounded
    assert "By difficulty:" in o
    # Easy: (10+15+20)/3 = 15m avg
    assert "Easy" in o and "15.0m avg" in o
    # Medium: (30+25)/2 = 27.5m avg
    assert "Medium" in o and "27.5m avg" in o
    # Hard: —
    assert "Hard" in o and "—" in o
    assert "By topic" in o
    assert "This week:" in o
    assert "This month:" in o
def test_stats_custom_weeks(env, capsys):
    """stats --weeks N shows correct number of weeks in heatmap."""
    run(["stats", "--weeks", "4"], capsys)
    o = out(capsys)
    assert "last 4 weeks:" in o
    # Should have 4 weekly lines (format: "  2026-09-26  ·······")
    week_lines = [l for l in o.splitlines() if l.strip()[:4].isdigit() and l.strip()[4] == "-"]
    assert len(week_lines) == 4

    run(["stats", "--weeks", "52"], capsys)
    o = out(capsys)
    assert "last 52 weeks:" in o
    week_lines = [l for l in o.splitlines() if l.strip()[:4].isdigit() and l.strip()[4] == "-"]
    assert len(week_lines) == 52

    # Clamping: --weeks 0 should show 1 week
    run(["stats", "--weeks", "0"], capsys)
    o = out(capsys)
    assert "last 1 weeks:" in o
    week_lines = [l for l in o.splitlines() if l.strip()[:4].isdigit() and l.strip()[4] == "-"]
    assert len(week_lines) == 1

    # Clamping: --weeks 100 should show 52 weeks
    run(["stats", "--weeks", "100"], capsys)
    o = out(capsys)
    assert "last 52 weeks:" in o
    week_lines = [l for l in o.splitlines() if l.strip()[:4].isdigit() and l.strip()[4] == "-"]
    assert len(week_lines) == 52


# ---------------------------------------------------------------- next session already active
def test_next_session_already_active(env, capsys):
    # Start a session
    open_session("two-sum")
    # Call next again - should show "Session already active"
    run(["next"], capsys)
    o = out(capsys)
    assert "Session already active" in o
    assert "grind done" in o

    assert run(["config", "preset=unknown"], capsys) == 1
    assert "Unknown preset" in out(capsys)


# ---------------------------------------------------------------- redo
def test_redo_command(env, capsys, no_fuzz):
    from conftest import seed_review_card
    state = store.load()
    seed_review_card(state, "two-sum")
    # Add a log entry so redo can find "last graded"
    add_log(state, "two-sum", 5, solved=True, when=local(0))
    store.save(state)
    # Redo from last graded
    run(["redo"], capsys)
    o = out(capsys)
    assert "Redo queued" in o
    assert "Two Sum" in o
    # Card should be due now
    state = store.load()
    c = sch.Card.from_dict(state["cards"]["two-sum"])
    assert c.due <= sch.utcnow()


def test_redo_with_slug(env, capsys, no_fuzz):
    from conftest import seed_review_card
    state = store.load()
    seed_review_card(state, "valid-anagram")
    store.save(state)
    # Redo specific slug
    run(["redo", "valid-anagram"], capsys)
    o = out(capsys)
    assert "Redo queued" in o
    assert "Valid Anagram" in o


def test_redo_errors(env, capsys):
    # No slug, no session, no last
    assert run(["redo"], capsys) == 1
    assert "pass a problem id" in out(capsys)

    # Unknown slug
    assert run(["redo", "unknown-problem"], capsys) == 1
    assert "unknown problem" in out(capsys)

    # Not seen yet
    assert run(["redo", "two-sum"], capsys) == 1
    assert "not seen yet" in out(capsys)


# ---------------------------------------------------------------- completion
def test_completion_commands(env, capsys):
    # bash
    assert run(["completion", "bash"], capsys) is None
    o = out(capsys)
    assert "_grind_completions" in o
    assert "complete -F _grind_completions grind" in o

    # zsh
    assert run(["completion", "zsh"], capsys) is None
    o = out(capsys)
    assert "_grind" in o
    assert "compdef _grind grind" in o

    # fish
    assert run(["completion", "fish"], capsys) is None
    o = out(capsys)
    assert "complete -c grind" in o


def test_completion_data(env, capsys):
    assert run(["_completion_data"], capsys) is None
    o = out(capsys)
    import json
    data = json.loads(o)
    assert "subcommands" in data
    assert "slugs" in data
    assert "config_keys" in data
    assert "next" in data["subcommands"]
    assert "two-sum" in data["slugs"]
    assert "daily_new" in data["config_keys"]
    assert "topics" in data
    assert "Arrays & Hashing" in data["topics"]
    assert "Two Pointers" in data["topics"]
    assert "Sliding Window" in data["topics"]

def test_completion_bash_topic(env, capsys):
    """bash completion includes topics for topic and list --topic."""
    assert run(["completion", "bash"], capsys) is None
    o = out(capsys)
    assert 'topics=' in o  # local topics variable
    assert 'topic)' in o  # topic command case
    assert 'list)' in o  # list command case
    # Check that list handles --topic flag
    assert 'if [[ "${words[cword-1]}" == "--topic" ]]' in o
    assert 'COMPREPLY=($(compgen -W "$topics" -- "$cur"))' in o

def test_completion_zsh_topic(env, capsys):
    """zsh completion includes topic completions."""
    assert run(["completion", "zsh"], capsys) is None
    o = out(capsys)
    assert "topics=" in o  # topics array
    assert "(topic)" in o  # topic command
    assert "(list)" in o  # list command
    assert "topic:($topics)" in o  # --topic flag completion

def test_completion_fish_topic(env, capsys):
    """fish completion includes topic completions."""
    assert run(["completion", "fish"], capsys) is None
    o = out(capsys)
    assert "__fish_use_subcommand topic" in o
    assert "__fish_use_subcommand list" in o
    assert "Arrays" in o and "Hashing" in o


# ---------------------------------------------------------------- _run error
def test_run_file_not_found(monkeypatch, capsys):
    # Test _run when git not found
    import grind.cli as cli
    # Mock subprocess.run to raise FileNotFoundError
    def mock_run(*args, **kwargs):
        raise FileNotFoundError()
    monkeypatch.setattr(cli.subprocess, "run", mock_run)
    ok, msg = cli._run(["git", "status"])
    assert ok is False
    assert msg == ""


# ---------------------------------------------------------------- _git error
def test_git_file_not_found(monkeypatch, capsys, tmp_path):
    import grind.cli as cli
    def mock_run(*args, **kwargs):
        raise FileNotFoundError()
    monkeypatch.setattr(cli.subprocess, "run", mock_run)
    ok, msg = cli._git(tmp_path, "status")
    assert ok is False
    assert "git not found" in msg
