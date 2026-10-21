"""grind backup — invisible, always-on: local history after every done,
cloud push to any git remote once the user picks one (first boot or backup)."""
from __future__ import annotations

import json
import os
import shutil
import subprocess

import pytest

from grind import store

from conftest import write_solution
from test_cli import SOLVED_BODY, out, run

SOL = "contains-duplicate"


@pytest.fixture
def remote(tmp_path):
    """A bare git remote standing in for the user's private GitHub repo."""
    r = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(r)], check=True, capture_output=True)
    return str(r)


@pytest.fixture
def no_gh(tmp_path, monkeypatch):
    """PATH with git but NO gh — deterministic on any machine, never touches a
    real GitHub account."""
    d = tmp_path / "bin"
    d.mkdir()
    os.symlink(shutil.which("git"), d / "git")
    monkeypatch.setenv("PATH", str(d))
    return d




def _make_progress(env, capsys):
    run(["next"], capsys)
    write_solution(env[1], SOL, SOLVED_BODY, [(([1, 2, 3, 1],), True)])
    assert run(["done", "--mins", "8"], capsys) is None


def _repo_log(data_dir):
    r = subprocess.run(["git", "-C", str(data_dir / "repo"), "log", "--oneline"],
                       capture_output=True, text=True)
    return r.stdout


# ---------------------------------------------------------------- local history

def test_done_creates_local_history_silently(env, capsys, no_gh):
    _make_progress(env, capsys)
    o = out(capsys)
    assert "grind backup" in _repo_log(env[0])       # history was committed
    # first run nudges once about cloud; everything else is silent
    assert o.count("backup:") == 1 and "local only" in o
    assert store.load()["hinted_cloud"] is True


def test_cloud_nudge_prints_exactly_once(env, capsys, no_gh):
    _make_progress(env, capsys)                     # problem 1 (hint shown)
    out(capsys)                                     # drain problem-1 output
    run(["next"], capsys)                           # problem 2
    out(capsys)                                     # drain the presentation
    write_solution(env[1], "valid-palindrome",
                   "class Solution:\n    def isPalindrome(self, s):\n        return True",
                   [(("a",), True)])
    run(["done", "--mins", "5"], capsys)
    assert "local only" not in out(capsys)          # never nagging again
    assert _repo_log(env[0]).count("grind backup") == 2


def test_backup_manual_local_only(env, capsys, no_gh):
    _make_progress(env, capsys)
    run(["skip"], capsys)
    assert run(["backup"], capsys) is None
    assert "backed up — local history" in out(capsys)


def test_backup_no_new_changes(env, capsys, no_gh):
    _make_progress(env, capsys)
    run(["skip"], capsys)
    assert run(["backup"], capsys) is None          # commits everything again? no —
    o = out(capsys)
    assert ("no new changes" in o) or ("backed up" in o)


# ---------------------------------------------------------------- cloud push

def test_done_pushes_to_configured_remote_silently(env, capsys, no_gh, remote):
    run(["config", f"backup_remote={remote}"], capsys)
    _make_progress(env, capsys)
    assert "backup:" not in out(capsys)             # silent on success
    log = subprocess.run(["git", "--git-dir", remote, "log", "--oneline"],
                         capture_output=True, text=True).stdout
    assert "grind backup" in log


def test_backup_failure_never_blocks_grading(env, capsys, no_gh):
    run(["config", "backup_remote=/nonexistent/remote.git"], capsys)
    run(["next"], capsys)
    write_solution(env[1], SOL, SOLVED_BODY, [(([1, 2, 3, 1],), True)])
    assert run(["done", "--mins", "8"], capsys) is None  # grading succeeds regardless
    assert "backup:" in out(capsys)
    assert store.load()["logs"]                     # the attempt was recorded


def test_backup_remote_flag_persists(env, capsys, no_gh, remote):
    _make_progress(env, capsys)
    assert run(["backup", "--remote", remote], capsys) is None
    assert store.load()["config"]["backup_remote"] == remote
    assert "backed up" in out(capsys)


# ---------------------------------------------------------------- first boot

def test_first_boot_accepts_any_git_url(env, capsys, no_gh, monkeypatch):
    import builtins
    monkeypatch.setattr(builtins, "input", lambda _: "git@gitlab.com:me/grind.git")
    run(["next"], capsys)
    s = store.load()
    assert s["config"]["backup_remote"] == "git@gitlab.com:me/grind.git"
    o = out(capsys)
    assert "noted — grind will back up" in o  # repo unreachable: informational, never fatal


def test_first_boot_rejects_bare_words(env, capsys, no_gh, monkeypatch):
    import builtins
    monkeypatch.setattr(builtins, "input", lambda _: "mygrind")
    run(["next"], capsys)
    o = out(capsys)
    assert "doesn't look like a git url" in o
    assert not store.load()["config"]["backup_remote"]  # nothing saved


def test_first_boot_accepts_existing_url_and_restores(env, capsys, no_gh, remote,
                                                     tmp_path, monkeypatch):
    # machine A: make a real backup
    run(["config", f"backup_remote={remote}"], capsys)
    _make_progress(env, capsys)

    # machine B: first boot, user answers with their existing repo's url
    data2, sol2 = tmp_path / "data2", tmp_path / "sol2"
    monkeypatch.setenv("GRIND_DATA_DIR", str(data2))
    monkeypatch.setenv("GRIND_SOLUTIONS", str(sol2))
    import builtins
    monkeypatch.setattr(builtins, "input", lambda _: remote)
    run(["next"], capsys)
    o = out(capsys)
    assert "restored your grind progress" in o
    s2 = store.load()
    assert len(s2["logs"]) == 1 and "contains-duplicate" in s2["cards"]
    assert s2["config"]["backup_remote"] == remote  # this machine's answer kept
    assert "Valid Palindrome" in o  # presentation continues restored progress


def test_first_boot_eof_skips_gracefully(env, capsys, no_gh):
    run(["next"], capsys)  # pytest stdin EOFs the prompt
    s = store.load()
    assert s["seen_intro"] is True
    assert not s["config"]["backup_remote"]


def test_first_boot_url_to_non_grind_repo_stays_fresh(env, capsys, no_gh, remote, tmp_path, monkeypatch):
    # a remote that exists but holds no grind backup -> no restore, fresh start
    work = tmp_path / "seed-work"
    subprocess.run(["git", "clone", "-q", remote, str(work)], check=True, capture_output=True)
    (work / "README.md").write_text("not a grind backup")
    G = ["git", "-C", str(work)]
    subprocess.run([*G, "add", "-A"], check=True, capture_output=True)
    subprocess.run([*G, "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-qm", "init"], check=True, capture_output=True)
    subprocess.run([*G, "push", "-q"], check=True, capture_output=True)
    import builtins
    monkeypatch.setattr(builtins, "input", lambda _: remote)
    run(["next"], capsys)
    o = out(capsys)
    assert "restored your grind progress" not in o
    assert "Contains Duplicate" in o                # normal first problem


def test_push_not_found_gives_creation_hint(env, capsys, no_gh, monkeypatch):
    from grind import cli as cli_mod
    run(["config", "backup_remote=https://example.com/x.git"], capsys)
    real_git = cli_mod._git

    def fake_git(repo, *args):
        if args[0] == "push":
            return False, "ERROR: Repository not found"
        return real_git(repo, *args)

    monkeypatch.setattr(cli_mod, "_git", fake_git)
    _make_progress(env, capsys)
    o = out(capsys)
    assert "backup: push failed" in o
    assert "create the repo first" in o


def test_backup_prompts_when_never_set(env, capsys, no_gh, remote, monkeypatch):
    import builtins
    monkeypatch.setattr(builtins, "input", lambda _: remote)
    _make_progress(env, capsys)                 # first boot skipped (EOF under pytest)
    out(capsys)
    assert run(["backup"], capsys) is None      # prompt -> url saved -> push succeeds
    o = out(capsys)
    assert "backed up — " + remote in o
    assert store.load()["config"]["backup_remote"] == remote


def test_restore_prompts_when_unset(env, capsys, no_gh):
    assert run(["restore"], capsys) == 1  # prompt EOFs under pytest
    assert "no backup to restore from" in out(capsys)


# ---------------------------------------------------------------- restore

def test_backup_restore_roundtrip(env, capsys, no_gh, remote, tmp_path, monkeypatch):
    run(["config", f"backup_remote={remote}"], capsys)
    _make_progress(env, capsys)

    # --- brand-new machine: fresh data + solutions dirs
    data2, sol2 = tmp_path / "data2", tmp_path / "sol2"
    monkeypatch.setenv("GRIND_DATA_DIR", str(data2))
    monkeypatch.setenv("GRIND_SOLUTIONS", str(sol2))
    assert run(["restore", remote], capsys) is None
    assert "restored from" in out(capsys)

    s1 = json.load(open(env[0] / "state.json"))
    s2 = json.load(open(data2 / "state.json"))
    assert s1["logs"] == s2["logs"] and s1["cards"] == s2["cards"]
    arch2 = sol2 / "archive" / SOL / "attempt-1.py"
    assert "len(set(nums))" in arch2.read_text()  # the graded attempt restored intact
    assert not (sol2 / f"{SOL}.py").exists()      # nothing active: done archived it
    run(["status"], capsys)
    o = out(capsys)
    assert "1/150 seen" in o and "proven 1/150" in o


def test_restore_refuses_clobber_without_force(env, capsys, no_gh, remote):
    run(["config", f"backup_remote={remote}"], capsys)
    _make_progress(env, capsys)
    assert run(["restore", remote], capsys) == 1     # local state already exists here
    assert "--force" in out(capsys)
    assert run(["restore", remote, "--force"], capsys) is None
    assert "restored" in out(capsys)


def test_restore_needs_a_source(env, capsys, no_gh):
    assert run(["restore"], capsys) == 1
    assert "no backup to restore from" in out(capsys)


# ---------------------------------------------------------------- hygiene

def test_backup_excludes_pycache(env, capsys, no_gh):
    run(["next"], capsys)
    write_solution(env[1], SOL, SOLVED_BODY, [(([1, 2, 3, 1],), True)])
    junk = env[1] / "__pycache__"
    junk.mkdir()
    (junk / "x.pyc").write_text("junk")
    run(["done", "--mins", "8"], capsys)
    repo = env[0] / "repo"
    assert (repo / "state.json").exists()
    assert (repo / "solutions" / "archive" / SOL / "attempt-1.py").exists()
    assert not (repo / "solutions" / "__pycache__").exists()


def test_git_missing_is_a_clear_error(env, capsys, tmp_path, monkeypatch):
    empty = tmp_path / "empty-bin"
    empty.mkdir()
    monkeypatch.setenv("PATH", str(empty))         # no git, no gh, nothing
    run(["next"], capsys)
    write_solution(env[1], "contains-duplicate", SOLVED_BODY, [(([1, 2, 3, 1],), True)])
    assert run(["done", "--mins", "8"], capsys) is None
    o = out(capsys)
    assert "backup: git not found" in o
    assert store.load()["logs"]                    # grading unaffected


