"""Shared fixtures: isolated state/solutions dirs, deterministic FSRS, helpers."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import builtins
import pytest
from fsrs import Card, Rating, Scheduler

from grind import scheduler as sch
from grind import store


@pytest.fixture
def env(tmp_path, monkeypatch):
    """Isolated GRIND_DATA_DIR + GRIND_SOLUTIONS; returns both paths."""
    data, sol = tmp_path / "data", tmp_path / "solutions"
    monkeypatch.setenv("GRIND_DATA_DIR", str(data))
    monkeypatch.setenv("GRIND_SOLUTIONS", str(sol))
    return data, sol


@pytest.fixture
def no_fuzz(monkeypatch):
    """Deterministic FSRS: disable interval fuzzing inside grind.scheduler."""
    real = Scheduler

    def make(desired_retention=0.9, enable_fuzzing=True, **kw):
        return real(desired_retention=desired_retention, enable_fuzzing=False, **kw)

    monkeypatch.setattr(sch, "Scheduler", make)
    return make


@pytest.fixture(autouse=True)
def _no_stdin(monkeypatch):
    """Tests never hang on input(): EOF by default; a test can monkeypatch
    builtins.input afterwards to provide answers."""
    def _eof(prompt=""):
        raise EOFError
    monkeypatch.setattr(builtins, "input", _eof)


@pytest.fixture
def state(env):
    return store.load()


# ---------------------------------------------------------------- helpers

def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def local(days_ago: float = 0.0) -> datetime:
    """Local-aware timestamp `days_ago` days in the past."""
    return datetime.now().astimezone() - timedelta(days=days_ago)


def add_log(state: dict, slug: str, elapsed: float, solved: bool = True,
            rating: float = 3.0, new: bool = False, when: datetime | None = None) -> None:
    state["logs"].append({"slug": slug, "rating": rating, "solved": solved,
                          "elapsed": elapsed, "new": new,
                          "ts": (when or now_utc()).isoformat()})


def write_solution(sol_dir, slug: str, body: str, tests: list) -> None:
    """Write a solutions/<slug>.py with Solution class + TESTS list."""
    p = Path(sol_dir)
    p.mkdir(parents=True, exist_ok=True)
    (p / f"{slug}.py").write_text(f"{body.rstrip()}\n\nTESTS = {tests!r}\n")


def review_card(reps: int = 2, rating=Rating.Good) -> Card:
    """A card graduated into the FSRS Review state (after `reps` reviews)."""
    s = Scheduler(desired_retention=0.9, enable_fuzzing=False)
    c = Card()
    for _ in range(reps):
        c, _ = s.review_card(c, rating)
    assert c.state.name == "Review"
    return c


def seed_review_card(state: dict, slug: str, reps: int = 2) -> None:
    state["cards"][slug] = review_card(reps).to_dict()


def open_session(slug: str) -> dict:
    """Start a session for `slug` directly in state (bypasses pick)."""
    state = store.load()
    state["session"] = {"slug": slug, "started": now_utc().isoformat(),
                        "why": "test", "scaffold": f"solutions/{slug}.py"}
    store.save(state)
    return state


def first_of_topic(topic: str) -> dict:
    return next(p for p in sch.bank() if p["topic"] == topic)


ALL_TOPICS = [
    "Arrays & Hashing", "Two Pointers", "Sliding Window", "Stack", "Binary Search",
    "Linked List", "Trees", "Heap / Priority Queue", "Backtracking", "Tries",
    "Graphs", "Advanced Graphs", "1-D Dynamic Programming", "2-D Dynamic Programming",
    "Greedy", "Intervals", "Math & Geometry", "Bit Manipulation",
]
