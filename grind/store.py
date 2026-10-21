"""State persistence: JSON file in the data dir (~/.grind-code by default)."""
from __future__ import annotations

import json
import os
from pathlib import Path

DEFAULT_CONFIG = {
    "daily_new": 5,                       # max new problems introduced per day
    # practice-time priors (min) from community data (DesignGurus, Blind, r/leetcode);
    # until your 2nd solve, then each problem's target floats to your own median
    "targets": {"Easy": 15, "Medium": 30, "Hard": 45},
    "retention_target": 0.90,             # FSRS desired retention
    "auto_web": False,                    # grind next opens the problem page automatically
    "auto_edit": False,                   # grind next opens the scaffold in $EDITOR automatically
    "backup_remote": "",                  # git url of your (private) backup repo
    "update_check": True,                 # daily HTTPS check for a newer version (grind update applies it)
}


def data_dir() -> Path:
    return Path(os.environ.get("GRIND_DATA_DIR", Path.home() / ".grind-code"))


def state_path() -> Path:
    return data_dir() / "state.json"


def load() -> dict:
    p = state_path()
    if not p.exists():
        return {"config": dict(DEFAULT_CONFIG), "cards": {}, "logs": [], "session": None,
                "graded_files": {}}
    s = json.loads(p.read_text())
    s["config"] = {**DEFAULT_CONFIG, **s.get("config", {})}
    s.setdefault("cards", {}), s.setdefault("logs", []), s.setdefault("session", None)
    s.setdefault("graded_files", {})   # slugs whose on-disk file is a graded attempt
    return s


def save(state: dict) -> None:
    data_dir().mkdir(parents=True, exist_ok=True)
    tmp = state_path().with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=1))
    tmp.replace(state_path())
