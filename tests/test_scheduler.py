"""grind.scheduler — the core: readiness, selection, floating grading, stats."""
from __future__ import annotations

from datetime import timedelta

import pytest
from fsrs import Card, Rating

from grind import scheduler as sch

from conftest import (ALL_TOPICS, add_log, first_of_topic, local, now_utc,
                      review_card, seed_review_card)

# a genuinely Medium problem (prior 30, floor 18) for target tests
MS = "product-of-array-except-self"


# ---------------------------------------------------------------- bank

def test_bank_shape():
    bank = sch.bank()
    assert len(bank) == 150
    assert len({p["slug"] for p in bank}) == 150
    assert {p["difficulty"] for p in bank} == {"Easy", "Medium", "Hard"}
    assert set(ALL_TOPICS) == {p["topic"] for p in bank}
    for p in bank:
        assert set(p) == {"slug", "num", "title", "difficulty", "topic"}
        assert isinstance(p["num"], int) and p["title"] and p["slug"]


def test_bank_roadmap_topic_blocks_contiguous():
    seen, order = set(), []
    for p in sch.bank():
        if p["topic"] not in seen:
            seen.add(p["topic"])
            order.append(p["topic"])
    assert order == ALL_TOPICS  # extracted order = NeetCode roadmap, no interleaving


def test_by_slug_covers_bank():
    assert len(sch.by_slug()) == 150
    assert sch.by_slug()["two-sum"]["difficulty"] == "Easy"
    assert sch.by_slug()[MS]["difficulty"] == "Medium"


# ---------------------------------------------------------------- readiness

def test_readiness_unseen_is_zero(state):
    assert sch.readiness(state, MS, now_utc()) == 0.0


def test_readiness_solved_last_attempt(state, no_fuzz):
    seed_review_card(state, MS)
    add_log(state, MS, 10.0, solved=True)
    assert 0.0 < sch.readiness(state, MS, now_utc()) <= 1.0


def test_readiness_failed_last_attempt_is_zero(state, no_fuzz):
    seed_review_card(state, MS)
    add_log(state, MS, 10.0, solved=True)
    add_log(state, MS, 12.0, solved=False)  # last attempt failed
    assert sch.readiness(state, MS, now_utc()) == 0.0


def test_readiness_decays_with_time(state, no_fuzz):
    seed_review_card(state, MS)
    add_log(state, MS, 10.0, solved=True)
    t0 = now_utc()
    fresh = sch.readiness(state, MS, t0)
    later = sch.readiness(state, MS, t0 + timedelta(days=60))
    assert later < fresh  # forgetting curve: further out, less ready


def test_readiness_by_topic_and_overall(state, no_fuzz):
    t0 = now_utc()
    assert set(sch.readiness_by_topic(state, t0)) == set(ALL_TOPICS)
    assert all(v == 0.0 for v in sch.readiness_by_topic(state, t0).values())
    assert sch.overall_readiness(state, t0) == 0.0

    p = first_of_topic("Arrays & Hashing")
    seed_review_card(state, p["slug"])
    add_log(state, p["slug"], 5.0, solved=True)
    expected = sum(sch.readiness(state, x["slug"], t0) for x in sch.bank()) / len(sch.bank())
    assert sch.overall_readiness(state, t0) == pytest.approx(expected)
    assert sch.readiness_by_topic(state, t0)[p["topic"]] > 0.0


def test_seen_counts_by_topic(state, no_fuzz):
    seed_review_card(state, "two-sum")
    counts = sch.seen_counts_by_topic(state)
    assert counts["Arrays & Hashing"] == 1
    assert sum(counts.values()) == 1


# ---------------------------------------------------------------- queue

def test_due_reviews_most_overdue_first(state, no_fuzz):
    for slug, hours in (("two-sum", 5), ("valid-anagram", 1)):
        seed_review_card(state, slug)
        c = Card.from_dict(state["cards"][slug])
        c.due = now_utc() - timedelta(hours=hours)
        state["cards"][slug] = c.to_dict()
    assert sch.due_reviews(state, now_utc()) == ["two-sum", "valid-anagram"]

    for slug in ("two-sum", "valid-anagram"):  # push both into the future
        c = Card.from_dict(state["cards"][slug])
        c.due = now_utc() + timedelta(days=1)
        state["cards"][slug] = c.to_dict()
    assert sch.due_reviews(state, now_utc()) == []


def test_new_today_counts_only_today_and_only_new(state):
    add_log(state, "two-sum", 5, new=True, when=local(0))
    add_log(state, "two-sum", 5, new=True, when=local(2))          # two days ago
    add_log(state, "valid-anagram", 5, new=False, when=local(0))  # review, not new
    assert sch.new_today(state, now_utc()) == 1


def _seed_one_solved_per_topic(state: dict, skip_topic: str | None = None) -> None:
    """Give every topic one solved-fresh problem (so no topic sits at readiness 0)."""
    done = set()
    for p in sch.bank():
        if p["topic"] not in done and p["topic"] != skip_topic:
            done.add(p["topic"])
            seed_review_card(state, p["slug"])
            add_log(state, p["slug"], 5.0, solved=True)


def test_pick_new_respects_daily_cap(state, no_fuzz):
    add_log(state, "two-sum", 5, new=True, when=local(0))
    state["config"]["daily_new"] = 1
    assert sch.pick_new(state, now_utc()) is None


def test_pick_new_starts_roadmap_on_cold_start(state, no_fuzz):
    assert sch.pick_new(state, now_utc()) == sch.bank()[0]


def test_pick_new_prefers_failed_topic_over_solved_topics(state, no_fuzz):
    _seed_one_solved_per_topic(state, skip_topic="Arrays & Hashing")
    # A&H's only seen problem was FAILED -> A&H is the sole topic at readiness 0
    a = first_of_topic("Arrays & Hashing")
    seed_review_card(state, a["slug"])
    add_log(state, a["slug"], 5.0, solved=False)
    assert sch.pick_new(state, now_utc())["topic"] == "Arrays & Hashing"


def test_pick_new_within_topic_curated_order(state, no_fuzz):
    # Only Arrays & Hashing has unseen problems left; pick must respect bank order
    ah = [p for p in sch.bank() if p["topic"] == "Arrays & Hashing"]
    for p in sch.bank():
        if p["topic"] != "Arrays & Hashing":
            seed_review_card(state, p["slug"])
    for p in ah[:3]:
        seed_review_card(state, p["slug"])
    assert sch.pick_new(state, now_utc()) == ah[3]


def test_pick_new_none_when_all_seen(state, no_fuzz):
    for p in sch.bank():
        seed_review_card(state, p["slug"])
    assert sch.pick_new(state, now_utc()) is None


def test_pick_next_review_beats_new(state, no_fuzz):
    seed_review_card(state, MS)
    c = Card.from_dict(state["cards"][MS])
    c.due = now_utc() - timedelta(minutes=1)
    state["cards"][MS] = c.to_dict()
    prob, why = sch.pick_next(state, now_utc())
    assert (prob["slug"], why) == (MS, "review")


def test_pick_next_new_when_nothing_due(state, no_fuzz):
    prob, why = sch.pick_next(state, now_utc())
    assert why == "new" and prob["topic"] == "Arrays & Hashing"


def test_pick_next_reports_next_upcoming_when_capped(state, no_fuzz):
    state["config"]["daily_new"] = 0
    seed_review_card(state, MS)  # due in the future
    prob, upcoming = sch.pick_next(state, now_utc())
    assert prob is None and upcoming == MS


# ---------------------------------------------------------------- floating target

def test_target_prior_until_second_solve(state):
    p = sch.by_slug()[MS]  # Medium -> prior 30
    add_log(state, MS, 30.0, solved=True)
    assert sch.target_info(state, p) == (30.0, "prior")


def test_target_calibrates_to_median_of_attempts(state):
    p = sch.by_slug()[MS]  # Medium: prior 30, floor 18
    add_log(state, MS, 25.0, solved=True)
    add_log(state, MS, 30.0, solved=True)
    assert sch.target_info(state, p) == (27.5, "calibrating")  # median of [25,30]


def test_target_calibrating_floor_blocks_bar_decay(state):
    p = sch.by_slug()[MS]  # Medium: prior 30, floor 18
    for e in (25.0, 30.0, 5.0, 5.0):  # median 15 -> floor 18 holds the bar
        add_log(state, MS, e, solved=True)
    assert sch.target_info(state, p) == (18.0, "calibrating")


def test_target_calibrates_upward_for_slow_solver(state):
    p = sch.by_slug()[MS]
    for e in (40.0, 60.0):  # median of [40,60]
        add_log(state, MS, e, solved=True)
    assert sch.target_info(state, p) == (50.0, "calibrating")


def test_target_locks_after_stable_window_with_outlier_drop(state):
    p = sch.by_slug()[MS]  # Medium: prior 30, floor 18
    for e in (25.0, 24.0, 26.0, 25.0, 90.0):  # 90 = one-off bad day
        add_log(state, MS, e, solved=True)
    # last 5, drop 90 -> [24,25,25,26]: band ok, median 25 * 1.1 = 27.5
    t, phase = sch.target_info(state, p)
    assert phase == "locked"
    assert t == pytest.approx(27.5)


def test_target_lock_value_uses_median_times_grace(state):
    p = sch.by_slug()[MS]  # Medium prior 30, floor 18
    for e in (45.0, 44.0, 46.0, 45.0, 45.0):
        add_log(state, MS, e, solved=True)
    # last 5 = [44,45,45,45,46], drop 46 -> median 45 * 1.1 = 49.5
    t, phase = sch.target_info(state, p)
    assert phase == "locked"
    assert t == pytest.approx(49.5)


def test_target_lock_survives_one_off_slip(state):
    p = sch.by_slug()[MS]
    for e in (44.0, 45.0, 45.0, 46.0, 45.0):
        add_log(state, MS, e, solved=True)
    assert sch.target_info(state, p)[1] == "locked"
    add_log(state, MS, 200.0, solved=True)  # single bad day
    t, phase = sch.target_info(state, p)
    assert phase == "locked"          # outlier dropped
    assert t == pytest.approx(49.5)   # bar unchanged


def test_target_drift_unlocks_then_relocks_higher(state):
    p = sch.by_slug()[MS]
    for e in (44.0, 45.0, 45.0, 46.0, 45.0):
        add_log(state, MS, e, solved=True)
    assert sch.target_info(state, p)[1] == "locked"

    for e in (120.0, 130.0, 140.0):  # persistent slowdown breaks the band
        add_log(state, MS, e, solved=True)
    assert sch.target_info(state, p)[1] == "calibrating"

    for e in (125.0, 130.0):  # new pace stabilizes -> relocks around it
        add_log(state, MS, e, solved=True)
    t, phase = sch.target_info(state, p)
    # last 5 [120,130,140,125,130], drop 140 -> core [120,125,130,130]
    assert phase == "locked"
    assert t == pytest.approx(140.25)  # core [120,125,130,130] -> 127.5 * 1.1


def test_unsolved_attempts_do_not_move_target(state):
    p = sch.by_slug()[MS]
    add_log(state, MS, 25.0, solved=True)
    add_log(state, MS, 30.0, solved=True)
    add_log(state, MS, 999.0, solved=False)
    assert sch.target_info(state, p) == (27.5, "calibrating")


# ---------------------------------------------------------------- floating grade

def test_fluency_score_shape():
    assert sch.fluency_score(False, 0.5) == 0.0
    assert sch.fluency_score(True, 0.0) == 1.0
    assert abs(sch.fluency_score(True, 1.0) - 2 / 3) < 1e-9
    prev = 1.0
    for r in (0.2, 0.5, 1.0, 2.0, 5.0):
        f = sch.fluency_score(True, r)
        assert f < prev  # strictly decreasing in ratio
        prev = f


def test_rating_float_anchors():
    assert sch.rating_float(False, 10, 30) == 1.0       # unsolved
    assert sch.rating_float(True, 0.0, 30) == 4.0        # instant = easy cap
    assert sch.rating_float(True, 30, 30) == pytest.approx(3.0)  # at target = good


def test_rating_float_solved_never_below_floor():
    assert sch.rating_float(True, 1000, 30) == sch.RATING_SOLVE_FLOOR
    assert sch.RATING_SOLVE_FLOOR == 2.2


def test_rating_float_monotonic_in_time():
    prev = 4.0
    for e in (5, 15, 30, 60, 120):
        r = sch.rating_float(True, e, 30)
        assert r <= prev
        prev = r


# ---------------------------------------------------------------- FSRS application

def test_apply_review_marks_was_new(state, no_fuzz):
    _, was_new = sch.apply_review(state, MS, 3.4, now_utc())
    assert was_new is True
    _, was_new2 = sch.apply_review(state, MS, 3.4, now_utc())
    assert was_new2 is False
    assert MS in state["cards"]


def test_apply_review_integer_rating_matches_fsrs(state, no_fuzz):
    seed_review_card(state, MS)
    t0 = now_utc()
    card = Card.from_dict(state["cards"][MS])
    expected = sch.scheduler(0.9).review_card(card, Rating.Good, t0)[0]
    got, _ = sch.apply_review(state, MS, 3.0, t0)
    assert got.to_dict() == expected.to_dict()


def test_apply_review_fractional_interpolates_between_neighbors(state, no_fuzz):
    seed_review_card(state, MS)
    t0 = now_utc()
    card = Card.from_dict(state["cards"][MS])
    s = sch.scheduler(0.9)
    lo = s.review_card(card, Rating.Good, t0)[0]
    hi = s.review_card(card, Rating.Easy, t0)[0]

    got, _ = sch.apply_review(state, MS, 3.5, t0)
    assert got.state.name == "Review"
    assert lo.stability < got.stability < hi.stability  # strictly between
    assert lo.due < got.due < hi.due


def test_apply_review_fractional_quantizes_inside_learning_steps(state, no_fuzz):
    t0 = now_utc()
    s = sch.scheduler(0.9)
    lo = s.review_card(Card(), Rating.Good, t0)[0]
    hi = s.review_card(Card(), Rating.Easy, t0)[0]
    got, _ = sch.apply_review(state, MS, 3.5, t0)  # fresh card: learning
    assert got.due in (lo.due, hi.due)  # one of the integer outcomes, not a blend
    assert got.due == hi.due            # frac >= 0.5 rounds up


def test_lerp_card_endpoints_and_midpoint(no_fuzz):
    t0 = now_utc()
    s = sch.scheduler(0.9)
    parent = review_card(2)               # both children share identity fields
    lo = s.review_card(parent, Rating.Good, t0)[0]
    hi = s.review_card(parent, Rating.Easy, t0)[0]
    assert sch._lerp_card(lo, hi, 0.0).to_dict() == lo.to_dict()
    assert sch._lerp_card(lo, hi, 1.0).to_dict() == hi.to_dict()
    mid = sch._lerp_card(lo, hi, 0.5)
    assert mid.stability == pytest.approx((lo.stability + hi.stability) / 2)


# ---------------------------------------------------------------- formatting & stats

def test_fmt_interval():
    n = now_utc()
    assert sch.fmt_interval(n - timedelta(minutes=1), n) == "now"
    assert sch.fmt_interval(n + timedelta(minutes=5), n) == "5m"
    assert sch.fmt_interval(n + timedelta(hours=5, minutes=30), n) == "5.5h"
    assert sch.fmt_interval(n + timedelta(hours=15), n) == "15h"
    assert sch.fmt_interval(n + timedelta(days=3), n) == "3.0d"


def test_activity_by_day(state):
    add_log(state, "two-sum", 5, when=local(0))
    add_log(state, "two-sum", 5, when=local(0))
    add_log(state, "valid-anagram", 5, when=local(3))
    act = sch.activity_by_day(state)
    assert act[local(0).date().isoformat()] == 2
    assert act[local(3).date().isoformat()] == 1


def test_streaks_empty(state):
    assert sch.streaks(state) == (0, 0)


def test_streaks_consecutive_and_gapped(state):
    for d in (5, 4, 3):
        add_log(state, "two-sum", 5, when=local(d))
    for d in (1, 0):
        add_log(state, "two-sum", 5, when=local(d))
    cur, best = sch.streaks(state)
    assert cur == 2   # yesterday + today
    assert best == 3  # the earlier run


def test_streak_survives_practice_yesterday_only(state):
    add_log(state, "two-sum", 5, when=local(1))
    assert sch.streaks(state) == (1, 1)


def test_streak_dies_after_two_day_gap(state):
    add_log(state, "two-sum", 5, when=local(2))
    assert sch.streaks(state) == (0, 1)


def test_solved_counts(state):
    add_log(state, "two-sum", 5, solved=True)
    add_log(state, "two-sum", 6, solved=True)
    add_log(state, "valid-anagram", 5, solved=False)
    add_log(state, "reverse-linked-list", 5, solved=True)
    solved, distinct, proven = sch.solved_counts(state)
    assert solved == 3
    assert distinct == 2
    assert proven == 2  # two-sum (last solved) + reverse-linked-list


def test_trends_needs_four_solved(state):
    for _ in range(3):
        add_log(state, MS, 10, solved=True)
    assert sch.trends(state) is None


def test_trends_splits_history_in_halves(state):
    # early: one failure + one slow solve; recent: three fast solves
    add_log(state, MS, 60, solved=False, rating=1.0, when=local(9))
    add_log(state, MS, 60, solved=True, rating=2.0, when=local(9))
    add_log(state, MS, 8, solved=True, rating=3.5, when=local(1))
    add_log(state, MS, 8, solved=True, rating=3.6, when=local(0.5))
    add_log(state, MS, 8, solved=True, rating=3.6, when=local(0))
    tr = sch.trends(state)
    assert tr is not None
    (r0, r1), (s0, s1), (p0, p1) = tr["rating"], tr["solve_rate"], tr["pace"]
    assert r0 < r1   # rating improved
    assert s0 < s1   # solve rate improved
    assert p0 > p1   # pace improved (fraction of target time fell)
