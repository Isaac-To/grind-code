"""Scheduling: due reviews first, then new problems from the least interview-ready topic.

The goal is interview readiness, not speed: readiness = you produced a working
solution last attempt AND can still recall it now. Grading is continuous — a
produced solution never rates below RATING_SOLVE_FLOOR regardless of pace, and
pace only modulates within that; the FSRS rating is a float fed to FSRS by
interpolating adjacent integer outcomes (quantized inside learning steps,
where intervals are fixed minutes).
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from fsrs import Card, Rating, Scheduler, State

BANK_PATH = Path(__file__).parent / "bank.json"
TARGET_FLOOR = 0.6   # personal target never drops below 60% of the difficulty prior
CONVERGE_N = 4       # attempts (after outlier drop) that must be stable to lock
CONVERGE_BAND = 1.5  # stable = slowest <= 1.5x fastest
TARGET_GRACE = 1.1   # locked target = demonstrated median x 10% grace
RATING_SOLVE_FLOOR = 2.2  # a produced, working solution never rates below 'hard'


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def bank() -> list[dict]:
    return json.loads(BANK_PATH.read_text())


def by_slug() -> dict[str, dict]:
    return {p["slug"]: p for p in bank()}


def scheduler(retention: float) -> Scheduler:
    return Scheduler(desired_retention=retention, enable_fuzzing=True)


def card_of(state: dict, slug: str) -> Card | None:
    d = state["cards"].get(slug)
    return Card.from_dict(d) if d else None



def readiness(state: dict, slug: str, now: datetime) -> float:
    """Interview readiness of one problem: you're ready if you *produced* a
    working solution last attempt AND can recall it now. Failing to solve —
    even after FSRS claims you 'remember' — resets it to 0."""
    c = card_of(state, slug)
    if c is None:
        return 0.0
    attempts = [l for l in state["logs"] if l["slug"] == slug]
    if attempts and not attempts[-1].get("solved"):
        return 0.0
    return max(0.0, scheduler(state["config"]["retention_target"])
               .get_card_retrievability(c, now))


def readiness_by_topic(state: dict, now: datetime) -> dict[str, float]:
    """Mean readiness across every bank problem in a topic (unseen = 0)."""
    tot: dict[str, list[float]] = {}
    for p in bank():
        tot.setdefault(p["topic"], []).append(readiness(state, p["slug"], now))
    return {t: sum(v) / len(v) for t, v in tot.items()}


def overall_readiness(state: dict, now: datetime) -> float:
    """Mean readiness across the whole bank — the interview-ready number."""
    v = [readiness(state, p["slug"], now) for p in bank()]
    return sum(v) / len(v)


def seen_counts_by_topic(state: dict) -> dict[str, int]:
    tot: dict[str, int] = {}
    for p in bank():
        tot[p["topic"]] = tot.get(p["topic"], 0) + (1 if p["slug"] in state["cards"] else 0)
    return tot


def due_reviews(state: dict, now: datetime) -> list[str]:
    """Due slugs, most-overdue first."""
    out = []
    for slug, d in state["cards"].items():
        c = Card.from_dict(d)
        if c.due <= now:
            out.append((c.due, slug))
    return [s for _, s in sorted(out)]


def upcoming_reviews(state: dict, now: datetime, days: int = 14) -> list[tuple[datetime, str]]:
    """Reviews due within the next `days` days, sorted by due date.

    Returns list of (due_datetime, slug) for cards where due <= now + days.
    """
    cutoff = now + timedelta(days=days)
    out = []
    for slug, d in state["cards"].items():
        c = Card.from_dict(d)
        if c.due <= cutoff:
            out.append((c.due, slug))
    return sorted(out)

def mark_due_now(state: dict, slug: str, now: datetime) -> bool:
    """Mark a problem's card as due now (just past due).

    Returns True if the card existed and was updated, False if no card exists
    (problem never seen).
    """
    c = card_of(state, slug)
    if c is None:
        return False
    # Set due to 1 second ago so it's the most overdue
    # Set due to 1 hour ago so it's the most overdue among due items
    c.due = now - timedelta(hours=1)
    state["cards"][slug] = c.to_dict()
    return True


def _today_key(now: datetime) -> str:
    return now.astimezone().date().isoformat()


def new_today(state: dict, now: datetime) -> int:
    return sum(1 for l in state["logs"] if l.get("new") and _today_key(datetime.fromisoformat(l["ts"])) == _today_key(now))


def pick_new(state: dict, now: datetime, *, ignore_limit: bool = False) -> dict | None:
    """First unseen problem from the least interview-ready topic.

    Topic readiness = mean readiness over its whole problem set (unseen = 0),
    so a fresh card barely moves a topic's score and new topics surface
    quickly; a topic with failed attempts stays at the top of the queue.
    Ties break toward fewer problems seen, then roadmap order — so a cold
    start walks the NeetCode roadmap, interleaving topics as they strengthen.
    Within a topic, problems appear in NeetCode's curated order (Easy -> Hard).

    ignore_limit=True: skip the daily_new check.
    """
    if not ignore_limit and new_today(state, now) >= state["config"]["daily_new"]:
        return None
    ready = readiness_by_topic(state, now)
    seen = seen_counts_by_topic(state)
    remaining = [p for p in bank() if p["slug"] not in state["cards"]]
    if not remaining:
        return None
    roadmap = {t: i for i, t in enumerate(dict.fromkeys(p["topic"] for p in bank()))}
    topics = sorted(
        {p["topic"] for p in remaining},
        key=lambda t: (round(ready[t], 4), seen.get(t, 0), roadmap[t]),
    )
    for t in topics:
        for p in remaining:
            if p["topic"] == t:
                return p
    return None

def pick_next(state: dict, now: datetime, *, ahead: bool = False, new: bool = False) -> tuple[dict | None, str]:
    """The single best next problem, and why ('review' / 'new' / 'none').

    ahead=True: pull the earliest upcoming review regardless of due date.
    new=True: ignore daily_new limit and pick a new problem.
    """
    if not new:
        due = due_reviews(state, now)
        if due:
            return by_slug().get(due[0]), "review"
        if ahead:
            upcoming = sorted((Card.from_dict(d).due, s) for s, d in state["cards"].items())
            if upcoming:
                return by_slug().get(upcoming[0][1]), "review"
            # ahead requested but no cards at all
            return None, "none"
    p = pick_new(state, now, ignore_limit=new)
    if p:
        return p, "new"
    if not new and not ahead:
        upcoming = sorted((Card.from_dict(d).due, s) for s, d in state["cards"].items())
        return None, "none" if not upcoming else upcoming[0][1]
    return None, "none"


# ---------------------------------------------------------------- floating grade

def _median(v: list[float]) -> float:
    s = sorted(v)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def target_info(state: dict, prob: dict) -> tuple[float, str]:
    """Personal fluency bar and its phase.

    'prior'       — fewer than 2 solves: grade against the difficulty prior.
    'calibrating' — target = median of your recent attempts (the bar follows
                    your pace while it's still moving).
    'locked'      — your last 5 solves are stable (slowest <= 1.5x fastest
                    after dropping one outlier): that's your demonstrated peak,
                    so the bar locks at median x TARGET_GRACE and stops
                    chasing further speed. Sustaining it earns steady good+
                    ratings; only persistent drift (enough slow reps to break
                    the band) unlocks it — recalibrating upward, mercifully.
    """
    prior = float(state["config"]["targets"][prob["difficulty"]])
    times = [l["elapsed"] for l in state["logs"]
             if l["slug"] == prob["slug"] and l.get("solved")]
    if len(times) < 2:
        return prior, "prior"
    floor = prior * TARGET_FLOOR
    recent = times[-(CONVERGE_N + 1):]
    if len(recent) == CONVERGE_N + 1:
        core = sorted(recent)[:-1]  # drop the single worst attempt (one-off bad day)
        if core[-1] <= core[0] * CONVERGE_BAND:
            return max(floor, _median(core) * TARGET_GRACE), "locked"
    return max(floor, _median(times[-6:])), "calibrating"


def effective_target(state: dict, prob: dict) -> float:
    return target_info(state, prob)[0]


def fluency_score(solved: bool, ratio: float) -> float:
    """Continuous fluency in [0,1]: 1.0 = instant recall, ~0.67 at target time,
    decays smoothly toward 0 as time blows past target. Unsolved = 0."""
    if not solved:
        return 0.0
    return 2.0 / (2.0 + max(ratio, 0.0))


def rating_float(solved: bool, elapsed: float, target: float) -> float:
    """FSRS rating as a float in [1,4]. The goal is interview readiness, not
    speed: producing a working solution is what counts (never rates below
    RATING_SOLVE_FLOOR, a 'hard' pass); pace only modulates within that.
    Unproduced = 1.0, at target time = 3.0, instant = 4.0."""
    if not solved:
        return 1.0
    return max(RATING_SOLVE_FLOOR,
               min(4.0, 1.0 + 3.0 * fluency_score(True, elapsed / target)))


def _lerp_card(a: Card, b: Card, t: float) -> Card:
    """Linear interpolation of two FSRS outcomes (stability, difficulty, due)."""
    da, db = a.to_dict(), b.to_dict()
    out = dict(da)
    out["stability"] = da["stability"] + (db["stability"] - da["stability"]) * t
    out["difficulty"] = da["difficulty"] + (db["difficulty"] - da["difficulty"]) * t
    due_a = datetime.fromisoformat(da["due"])
    due_b = datetime.fromisoformat(db["due"])
    out["due"] = (due_a + (due_b - due_a) * t).isoformat()
    return Card.from_dict(out)


def apply_review(state: dict, slug: str, rating_f: float, now: datetime) -> tuple[Card, bool]:
    """Grade a problem with a fractional FSRS rating; returns (card, was_new).

    For cards in the review state the result is interpolated between the two
    adjacent integer ratings, so intervals vary continuously with your speed.
    Inside learning steps (fixed-minute intervals) the rating rounds instead.
    """
    was_new = slug not in state["cards"]
    c = card_of(state, slug) or Card()
    s = scheduler(state["config"]["retention_target"])
    lo = Rating(max(1, min(4, int(rating_f))))
    frac = rating_f - int(rating_f)
    if frac < 1e-9 or rating_f >= 4.0:
        c2, _log = s.review_card(c, lo, now)
    else:
        c_lo, _ = s.review_card(c, lo, now)
        c_hi, _ = s.review_card(c, Rating(min(4, lo.value + 1)), now)
        if c_lo.state == State.Review and c_hi.state == State.Review:
            c2 = _lerp_card(c_lo, c_hi, frac)
        else:
            c2 = c_hi if frac >= 0.5 else c_lo
    state["cards"][slug] = c2.to_dict()
    return c2, was_new


def fmt_interval(due: datetime, now: datetime) -> str:
    secs = (due - now).total_seconds()
    if secs < 0:
        return "now"
    if secs < 3600:
        return f"{int(secs // 60)}m"
    if secs < 86400:
        h = secs / 3600
        return f"{h:.0f}h" if h >= 10 else f"{h:.1f}h"
    return f"{secs / 86400:.1f}d"


# ---------------------------------------------------------------- progress stats

def activity_by_day(state: dict) -> dict[str, int]:
    """Graded attempts per local calendar day ('YYYY-MM-DD' -> count)."""
    out: dict[str, int] = {}
    for l in state["logs"]:
        d = datetime.fromisoformat(l["ts"]).astimezone().date().isoformat()
        out[d] = out.get(d, 0) + 1
    return out


def streaks(state: dict) -> tuple[int, int]:
    """(current, longest) streaks of consecutive days with graded practice."""
    days = sorted(date.fromisoformat(d) for d in activity_by_day(state))
    if not days:
        return 0, 0
    longest = run = 1
    for a, b in zip(days, days[1:]):
        run = run + 1 if (b - a).days == 1 else 1
        longest = max(longest, run)
    today = datetime.now().astimezone().date()
    cur = 0
    if (today - days[-1]).days <= 1:  # alive if you practiced today or yesterday
        cur, prev = 1, days[-1]
        for d in reversed(days[:-1]):
            if (prev - d).days == 1:
                cur, prev = cur + 1, d
            else:
                break
    return cur, longest


def solved_counts(state: dict) -> tuple[int, int, int]:
    """(total solved attempts, distinct problems solved, problems whose last
    attempt was solved — i.e. currently *proven* production-ready)."""
    solved = [l for l in state["logs"] if l.get("solved")]
    distinct = {l["slug"] for l in solved}
    last: dict[str, bool] = {}
    for l in state["logs"]:
        last[l["slug"]] = bool(l.get("solved"))
    proven = sum(1 for v in last.values() if v)
    return len(solved), len(distinct), proven


def trends(state: dict) -> dict | None:
    """Early vs. recent performance: mean rating, solve rate, median pace
    (elapsed vs. current bar). None until there are 4+ solved attempts."""
    logs = sorted(state["logs"], key=lambda l: l["ts"])
    solved = [l for l in logs if l.get("solved")]
    if len(solved) < 4:
        return None
    half = len(logs) // 2
    early, late = logs[:half], logs[half:]
    b = by_slug()

    def mean_rating(v):
        return sum(l["rating"] for l in v if l.get("solved")) / max(1, len([x for x in v if x.get("solved")]))

    def solve_rate(v):
        return sum(1 for l in v if l.get("solved")) / len(v)

    def median_pace(v):
        rs = sorted(l["elapsed"] / effective_target(state, b[l["slug"]])
                    for l in v if l.get("solved"))
        return rs[len(rs) // 2] if rs else 0.0

    return {"rating": (mean_rating(early), mean_rating(late)),
            "solve_rate": (solve_rate(early), solve_rate(late)),
            "pace": (median_pace(early), median_pace(late))}
