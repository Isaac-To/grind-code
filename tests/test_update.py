"""grind.update — announce newer versions (consent-gated, silent on failure),
apply them ONLY on explicit request, and never clobber local work.

`cmd_update` is always invoked with an injected `root=` here — never through
cli.main, which would point at the developer's real checkout.
"""
from __future__ import annotations

import subprocess
import urllib.request

import pytest

from grind import __version__, store, update
from test_cli import out, run


class _Resp:
    """Minimal urlopen() context-manager result."""
    def __init__(self, body):
        self._body = body.encode()

    def read(self, n=-1):
        return self._body if n < 0 else self._body[:n]

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


# ---------------------------------------------------------------- comparing

def test_is_newer():
    assert update.is_newer("0.2.0", "0.1.0")
    assert update.is_newer("0.1.1", "0.1.0")
    assert update.is_newer("1.0", "0.9.9")              # length padding
    assert not update.is_newer("0.1.0", "0.1.0")
    assert not update.is_newer("0.0.9", "0.1.0")
    assert not update.is_newer("junk", "0.1.0")         # unparseable never nags
    assert not update.is_newer("0.1.0", "junk")


def test_latest_on_main_parses(monkeypatch):
    monkeypatch.setattr(urllib.request, "urlopen",
                        lambda *a, **k: _Resp('__version__ = "0.9.9"\n'))
    assert update.latest_on_main() == "0.9.9"


def test_latest_on_main_no_version_in_body(monkeypatch):
    monkeypatch.setattr(urllib.request, "urlopen",
                        lambda *a, **k: _Resp("# no version here\n"))
    assert update.latest_on_main() is None


def test_latest_on_main_offline(monkeypatch):
    def boom(*a, **k):
        raise OSError("no network")
    monkeypatch.setattr(urllib.request, "urlopen", boom)
    assert update.latest_on_main() is None


# ---------------------------------------------------------------- announcing

def test_banner_announces_newer_version(env, capsys, monkeypatch):
    monkeypatch.setattr(update, "latest_on_main", lambda: "9.9.9")
    run(["status"], capsys)
    o = out(capsys)
    assert "update available: grind 9.9.9" in o and f"you have {__version__}" in o
    assert "grind update" in o and "update_check=false" in o
    u = store.load()["update"]
    assert u["latest"] == "9.9.9" and u["ts"]


def test_no_banner_when_current(env, capsys, monkeypatch):
    monkeypatch.setattr(update, "latest_on_main", lambda: __version__)
    run(["status"], capsys)
    assert "update available" not in out(capsys)


def test_no_banner_when_remote_is_older(env, capsys, monkeypatch):
    monkeypatch.setattr(update, "latest_on_main", lambda: "0.0.1")
    run(["status"], capsys)
    assert "update available" not in out(capsys)


def test_check_runs_once_per_day(env, capsys, monkeypatch):
    calls = []

    def fetch():
        calls.append(1)
        return "9.9.9"
    monkeypatch.setattr(update, "latest_on_main", fetch)
    run(["status"], capsys)
    capsys.readouterr()
    run(["status"], capsys)                       # same day: no re-fetch, no re-nag
    assert len(calls) == 1
    assert "update available" not in out(capsys)


def test_config_disables_check(env, capsys, monkeypatch):
    calls = []

    def fetch():
        calls.append(1)
        return "9.9.9"
    monkeypatch.setattr(update, "latest_on_main", fetch)
    run(["config", "update_check=false"], capsys)
    capsys.readouterr()
    run(["status"], capsys)
    assert not calls and "update available" not in out(capsys)
    assert store.load()["config"]["update_check"] is False


def test_fetch_failure_is_silent(env, capsys, monkeypatch):
    monkeypatch.setattr(update, "latest_on_main", lambda: None)
    assert run(["status"], capsys) is None        # never breaks the command
    assert "update available" not in out(capsys)
    assert store.load()["update"]["latest"] is None   # stamped: no retry storm today


def test_corrupt_stamp_rechecks(env, capsys, monkeypatch):
    s = store.load()
    s["update"] = {"ts": "garbage", "latest": None}
    store.save(s)
    monkeypatch.setattr(update, "latest_on_main", lambda: "9.9.9")
    run(["status"], capsys)
    assert "9.9.9" in out(capsys)


def test_version_flag(capsys):
    assert run(["--version"], capsys) == 0
    assert f"grind {__version__}" in out(capsys)


# ---------------------------------------------------------------- updater

@pytest.fixture
def checkout(tmp_path):
    """A bare 'upstream' + a clone of it; push_version(v) advances upstream."""
    def git(d, *a):
        subprocess.run(["git", "-C", str(d), *a], check=True, capture_output=True)

    bare = tmp_path / "upstream.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(bare)], check=True)
    seed = tmp_path / "seed"
    (seed / "grind").mkdir(parents=True)
    (seed / "grind" / "__init__.py").write_text('__version__ = "0.1.0"\n')
    git(seed, "init", "-q", "-b", "main")
    git(seed, "config", "user.email", "t@example.com")
    git(seed, "config", "user.name", "t")
    git(seed, "add", "-A")
    git(seed, "commit", "-q", "-m", "v1")
    git(seed, "remote", "add", "origin", str(bare))
    git(seed, "push", "-q", "origin", "main")

    clone = tmp_path / "grind-code"
    subprocess.run(["git", "clone", "-q", str(bare), str(clone)], check=True)
    git(clone, "config", "user.email", "t@example.com")
    git(clone, "config", "user.name", "t")

    def push_version(v):
        (seed / "grind" / "__init__.py").write_text(f'__version__ = "{v}"\n')
        git(seed, "commit", "-q", "-am", v)
        git(seed, "push", "-q", "origin", "main")

    return clone, push_version


def test_update_non_git_prints_manual_command(tmp_path):
    with pytest.raises(SystemExit) as e:
        update.cmd_update(None, root=tmp_path)
    o = str(e.value.code)          # sys.exit("msg"): assert on the message itself
    assert "not a git checkout" in o and "pip install --force-reinstall" in o


def test_update_pulls_and_reinstalls(checkout, capsys, monkeypatch):
    root, push = checkout
    push("0.2.0")
    calls = []
    monkeypatch.setattr(update, "_pip_install",
                        lambda r: calls.append(str(r)) or True)
    update.cmd_update(None, root=root)
    assert calls == [str(root)]                    # editable reinstall of the clone
    o = out(capsys)
    assert "grind 0.2.0" in o and "up to date" in o
    assert "0.2.0" in (root / "grind" / "__init__.py").read_text()


def test_update_refuses_dirty_tree(checkout):
    root, _ = checkout
    (root / "grind" / "__init__.py").write_text("__version__ = '0.1.0-dirty'\n")
    with pytest.raises(SystemExit) as e:
        update.cmd_update(None, root=root)
    assert "uncommitted changes" in str(e.value.code)
    assert "0.1.0-dirty" in (root / "grind" / "__init__.py").read_text()  # untouched


def test_update_untracked_files_do_not_block(checkout, capsys, monkeypatch):
    root, push = checkout
    push("0.2.0")
    (root / "notes.txt").write_text("untracked")
    monkeypatch.setattr(update, "_pip_install", lambda r: True)
    update.cmd_update(None, root=root)              # no refusal, no exception
    assert (root / "notes.txt").exists()            # and the file survived


def test_update_diverged_history_fails_safely(checkout, monkeypatch):
    root, push = checkout
    push("0.2.0")
    subprocess.run(["git", "-C", str(root), "commit", "-q", "--allow-empty", "-m", "local"],
                   check=True, capture_output=True)
    monkeypatch.setattr(update, "_pip_install", lambda r: True)
    with pytest.raises(SystemExit):
        update.cmd_update(None, root=root)
    assert "0.1.0" in (root / "grind" / "__init__.py").read_text()  # left exactly as-is


def test_update_pip_failure_gives_manual_command(checkout, monkeypatch):
    root, push = checkout
    push("0.2.0")
    monkeypatch.setattr(update, "_pip_install", lambda r: False)
    with pytest.raises(SystemExit) as e:
        update.cmd_update(None, root=root)
    assert "-m pip install -e" in str(e.value.code)  # the exact command to finish by hand
