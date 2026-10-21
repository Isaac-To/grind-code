"""Update awareness: a consent-gated version check, plus an explicit updater.

Security posture — deliberately narrow:
- Check (`maybe_check`): once a day, if `update_check` is true, one HTTPS GET
  to a hardcoded raw.githubusercontent.com URL (this repo's own __init__.py
  on main). 3s timeout, size-capped, parsed as text; nothing fetched is ever
  executed, nothing but the request itself is sent. All failures are silent —
  grind never requires the network.
- Update (`cmd_update`): never automatic — runs only when the user types
  `grind update`. Pulls with --ff-only from the user's own origin (wherever
  they cloned from; this module never supplies a fetch URL for code), refuses
  a dirty working tree, then reinstalls editable via the running interpreter's
  pip. No curl|sh, no code execution of downloaded bytes by grind itself.
"""
from __future__ import annotations
from datetime import datetime
import re
import subprocess
import sys
import urllib.request
from datetime import timedelta
from pathlib import Path

from . import __version__, store
from . import scheduler as sch

CHECK_URL = "https://raw.githubusercontent.com/Isaac-To/grind-code/main/grind/__init__.py"
CHECK_EVERY = timedelta(hours=24)
FETCH_TIMEOUT = 3          # seconds; the check must never be felt when offline
FETCH_CAP = 16_384         # bytes; __init__.py is ~500 — anything bigger is wrong
_VER = re.compile(r'__version__\s*=\s*"([^"]+)"')


def _vtuple(v: str) -> tuple[int, ...]:
    parts = []
    for p in v.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            break
    return tuple(parts)


def is_newer(latest: str, current: str) -> bool:
    """True only when `latest` is a well-formed version strictly greater than
    `current`. Anything unparseable compares false — a bad fetch must never
    nag."""
    a, b = _vtuple(latest), _vtuple(current)
    if not a or not b:
        return False
    n = max(len(a), len(b))
    a, b = a + (0,) * (n - len(a)), b + (0,) * (n - len(b))
    return a > b


def latest_on_main() -> str | None:
    """Version string on origin/main, or None if unreachable/unparseable."""
    try:
        with urllib.request.urlopen(CHECK_URL, timeout=FETCH_TIMEOUT) as r:
            text = r.read(FETCH_CAP).decode("utf-8", "replace")
        m = _VER.search(text)
        return m.group(1) if m else None
    except Exception:
        return None


def maybe_check() -> None:
    """Called at the end of every command: at most once a day, if the user
    allows, note a newer version on main. Prints at most two lines; never
    raises, never installs anything."""
    try:
        state = store.load()
        if not state["config"].get("update_check"):
            return
        last = state.get("update", {}).get("ts")
        if last:
            try:
                if sch.utcnow() - datetime.fromisoformat(last) < CHECK_EVERY:
                    return
            except ValueError:
                pass                                    # corrupt stamp: re-check
        latest = latest_on_main()
        state["update"] = {"ts": sch.utcnow().isoformat(), "latest": latest}
        store.save(state)
        if latest and is_newer(latest, __version__):
            print(f"update available: grind {latest} (you have {__version__}) — run: grind update")
            print("  (daily HTTPS version check — disable: grind config update_check=false)")
    except Exception:
        pass                                              # the loop never breaks over this


# ---------------------------------------------------------------- updater

def _git(root: Path, *args: str) -> tuple[bool, str]:
    r = subprocess.run(["git", "-C", str(root), *args],
                       capture_output=True, text=True)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def _local_version(root: Path) -> str:
    """Version of the just-pulled tree, from disk — the imported __version__
    predates the pull."""
    m = _VER.search((root / "grind" / "__init__.py").read_text())
    return m.group(1) if m else "unknown"


def _pip_install(root: Path) -> bool:
    """Reinstall editable via the interpreter grind is running under (its
    venv), so the pulled code and entry points actually take effect."""
    try:
        return subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."],
                              cwd=str(root)).returncode == 0
    except OSError:
        return False


def cmd_update(args, root: Path | None = None) -> None:
    """`grind update`: pull origin and reinstall. Explicit user action only;
    every refusal is non-destructive and says what to do."""
    root = root or Path(__file__).resolve().parent.parent
    if not (root / ".git").exists():
        sys.exit(f"not a git checkout: {root}\n"
                 "update manually: pip install --force-reinstall "
                 "git+https://github.com/Isaac-To/grind-code.git")
    ok, out_ = _git(root, "status", "--porcelain", "-uno")
    if not ok:
        sys.exit(f"git status failed in {root}\n{out_}")
    if out_:
        sys.exit("working tree has uncommitted changes — commit or stash them, then retry")
    r = subprocess.run(["git", "-C", str(root), "pull", "--ff-only"])
    if r.returncode != 0:
        sys.exit(1)                                     # git already said why
    if not _pip_install(root):
        sys.exit(f"pulled, but pip failed — finish with:\n"
                 f"  {sys.executable} -m pip install -e {root}")
    print(f"grind {_local_version(root)} — up to date")
