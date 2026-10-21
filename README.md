# grind

A local, Anki-style spaced-repetition trainer for LeetCode. The goal is one
thing: **getting you to interview-ready state** — every problem in the OA
curriculum is one you can produce a working solution for, from memory, on
demand. Speed is a signal along the way, never the goal.

- **Curriculum**: all 150 NeetCode problems across the 18 topics that cover ~95% of
  online-assessment patterns (arrays & hashing, two pointers, sliding window, stack,
  binary search, linked list, trees, tries, heap, backtracking, graphs, advanced
  graphs, 1-D/2-D DP, greedy, intervals, math & geometry, bit manipulation).
- **Scheduler**: [FSRS](https://github.com/open-spaced-repetition/py-fsrs) — the same
  algorithm modern Anki uses — via the `fsrs` package. No SRS math of our own.
- **Readiness is the metric.** A problem is *ready* when you solved it on your
  last attempt AND can still recall it now. Fail an attempt and its readiness
  resets to 0 — remembered-but-unproducible doesn't count. `grind status` tracks
  overall readiness toward an 80% interview-ready bar; `grind topics` shows
  which skills are furthest from ready, and new problems always come from the
  least-ready topic.

- **Curriculum**: all 150 NeetCode problems across the 18 topics that cover ~95% of
  online-assessment patterns (arrays & hashing, two pointers, sliding window, stack,
  binary search, linked list, trees, tries, heap, backtracking, graphs, advanced
  graphs, 1-D/2-D DP, greedy, intervals, math & geometry, bit manipulation).
- **Scheduler**: [FSRS](https://github.com/open-spaced-repetition/py-fsrs) — the same
  algorithm modern Anki uses — via the `fsrs` package. No SRS math of our own.
- **Grading is fully floating — no easy/medium/hard buckets.** Wall-clock solve time
  vs. an adaptive personal target gives a continuous fluency score; the FSRS rating
  is a float in [1, 4]:

  ```
  target phases (shown live in every prompt):
    prior        — priors: Easy 15 / Medium 30 / Hard 45 min (community
                   practice-time data) until your 2nd solve
    calibrating  — median of your recent attempts, floored at 0.6× the prior;
                   the bar follows your pace while it's still moving
    locked       — once your last 5 solves are stable (slowest ≤ 1.5× fastest
                   after dropping one outlier), that's your demonstrated peak:
                   the bar locks at your median × 1.1 and stops chasing
                   further speed. Sustaining it earns steady good+ ratings.
                   Only persistent drift unlocks it — and it recalibrates
                   upward, not as a penalty.

  fluency = 2 / (2 + elapsed/target)     ∈ [0, 1]   (0 if unsolved)
  rating   = 1 + 3 × fluency            ∈ [1, 4]   (1.0 = unsolved)
    elapsed = 0.5× target  ->  fluency 0.80, rating 3.40
    elapsed = 1.0× target  ->  fluency 0.67, rating 3.00
    elapsed = 2.0× target  ->  fluency 0.50, rating 2.50
  ```

The fractional rating feeds FSRS by interpolating between the two adjacent
integer outcomes, so review intervals vary continuously with your speed.
(Inside FSRS's fixed-minute learning steps the rating rounds instead.) While
calibrating, improvement tightens the bar — that's how fluency is built. Once
locked, the treadmill stops: the system assumes your pace is the peak and
grades you for sustaining it, not for shaving further seconds.

- **Topic balancing**: new problems always come from your weakest topic (mean
  recall probability over the topic's whole problem set, unseen = 0), so effort
  flows to neglected skills. Within a topic, problems unlock in NeetCode's
  curated ramp (Easy → Hard).

## Install

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

## Daily loop

```bash
grind next        # best problem right now: due reviews first, else least-ready topic's new
                  #   --web  open it in the browser   --edit  open the scaffold in $EDITOR
grind done        # stop timer, run the FULL test suite, grade, schedule the next rep
                  #   TESTS are ground truth for "solved" when they exist
                  #   --rating 3.5   override with a float rating (1..4)
                  #   --mins N      override elapsed time (e.g. after a break)
                  #   --solved / --fail only apply when no TESTS are defined
grind check       # quick subset of TESTS (first 3) while you're mid-solve
                  #   [slug]  defaults to the active session, then to the last graded
                  #   --n 5 / --all run more or all cases
grind status      # readiness, streak, proven count, what's due
grind topics      # per-topic readiness bars
grind stats       # streaks, solved counts, first-half→recent trends, 14-day sparkline
grind config      # show/set: daily_new, targets, retention_target, auto_web, auto_edit
grind skip        # drop the active session ungraded
```

Solve in your IDE: each `grind next` writes a `solutions/<slug>.py` scaffold with the
problem link, a `class Solution` stub and a `TESTS` list. Paste the problem's
example cases into `TESTS` once as `((args...), expected)` pairs — the runner
auto-discovers the method to call in your `Solution` class (the last public
method, so helpers go above it).

`grind done` then runs the **entire suite as the gate**: all cases pass →
solved (rating from time vs. your target); any failure → unsolved, rating 1.0,
resurfacing within minutes — fix it and `grind next` brings it straight back.
With no TESTS defined, `done` falls back to asking whether you solved it.
`grind check` is the lightweight loop while solving — just a few cases to
catch silly mistakes early.

Set-and-forget: `grind config auto_edit=true` makes every `grind next` open
the scaffold in `$EDITOR` (`auto_web=true` likewise opens the problem page),
so the daily loop is just: `grind next` → solve → `grind done`.

## Backup — invisible, always on

On first run, grind asks one question: the **git url of your backup repo** —
any host works (GitHub, GitLab, your own server over SSH, even a NAS path
like `/mnt/nas/grind.git`). Grind never creates the repo; you make it
yourself, and every `grind done` afterwards silently commits your progress
and solutions to a local history repo **and pushes to yours**. If the repo
you name already holds a grind backup — say, on a new machine — your
progress is restored on the spot and you continue where you left off.
Auth is just your normal git credentials; there's no `gh` dependency.

Success is silent; failures print one `backup:` line and never interrupt
grading. `grind backup` forces a snapshot now; `grind restore` pulls your
backup onto any machine. No cloud configured? Everything still works
locally, and a one-time hint reminds you how to enable off-machine backup.

## How "next best" is chosen

1. **Due reviews first** — retention of what you know beats novelty.
2. Otherwise, a **new problem from your least-ready topic**, up to `daily_new` per day.
3. Otherwise, nothing — rest. FSRS intervals grow from 1 day to months as you
   demonstrate reliable recall.

Readiness = you solved the problem last attempt AND can still recall it now;
topic readiness averages over the topic's whole problem set (unseen = 0, failed
last attempt = 0). `grind status` tracks overall readiness toward an 80%
interview-ready bar; `grind topics` shows which skills are furthest from ready,
and `grind stats` shows the trend lines — rating, solve rate, and pace moving
from your first half of attempts to your recent ones, plus streaks and
problems-solved counts.

## Data

- State: `~/.grind-code/state.json` (override with `GRIND_DATA_DIR`).
- Solutions: `./solutions/` (override with `GRIND_SOLUTIONS`).
- Problem bank: `grind/bank.json` — extracted from neetcode.io's own published list;
  slugs/difficulties validated against LeetCode's database. Fully offline afterwards.

## Layout

```
grind/bank.json     150 problems (slug, title, difficulty, topic, roadmap order)
grind/store.py      JSON persistence
grind/scheduler.py  FSRS wiring, readiness model, timer→rating, next-best, streaks/trends
grind/cli.py        commands
```
