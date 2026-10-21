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

## Updates

Once a day grind fetches its own `__init__.py` from GitHub main over HTTPS,
compares versions, and if there's a newer one prints a one-line heads-up
(`update available: grind 0.2.0 … — run: grind update`). That's all the
"automatic" there is: the check sends nothing but the request, nothing
fetched is ever executed, it's silent when offline, and
`grind config update_check=false` turns it off entirely.

`grind update` applies an update — only when you type it: `git pull
--ff-only` in your clone (from *your* origin, wherever you cloned it) and a
reinstall via the running venv's pip. It refuses a dirty working tree so your
local changes are never clobbered, and a diverged history fails safely
instead of merging. Not a git checkout? It prints the manual command instead.

## Daily loop

```bash
grind next        # best problem right now: due reviews first, else least-ready topic's new
                  #   sets up the WHOLE environment for that one problem (see below)
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

Solve in a ready-made environment: each `grind next` writes two files and
nothing else is needed — no browser hunting, no copy-pasting, no data-structure
plumbing:

- `solutions/<slug>.md` — the full problem statement with examples and
  constraints, offline.
- `solutions/<slug>.py` — the **real** LeetCode signature (`def twoSum(self,
  nums, target)`, design classes keep their names), the `ListNode`/`TreeNode`
  definitions when the problem needs them, and `TESTS` **pre-filled from the
  problem's examples plus hand-written edge cases** — empty inputs, single
  elements, boundaries, extremes (2–4 per problem, on top of the published
  examples). Design problems get operation sequences (`MinStack`,
  `LRUCache`, …) and "any valid answer" checks (any-order subsets, any legal
  N-Queens board, float tolerance) — nothing to copy from the web.
- `solutions/archive/<slug>/` — the problem's whole history: `attempt-1.py,
  -2, …` (graded attempts, filed automatically on `grind done`), `wip.py`
  (a parked `grind skip`), `statement.md`. `solutions/` itself holds only
  the problem you're working on right now.

You write the body; `grind check`/`grind done` convert the printed values
(`[1,2,3]` arrays) into linked lists/trees/graph nodes automatically and
compare with LeetCode's own semantics — in-place mutation, unordered rows,
node-by-value results included.

`grind done` runs the **entire suite as the gate**: all cases pass → solved
(rating from time vs. your target); any failure → unsolved, rating 1.0,
resurfacing within minutes — fix it and `grind next` brings it straight back.
With no TESTS defined, `done` falls back to asking whether you solved it.
`grind check` is the lightweight loop while solving — just a few cases to
catch silly mistakes early.

Grading is the cutoff: `grind done` files the attempt under
`solutions/archive/<slug>/attempt-N.py` (kept forever, backed up like
everything else) the moment it's graded — solved or not — and the statement
goes with it. `solutions/` always shows just the one problem in front of
you: at every `grind next`, stray files of other known problems are swept
into their archive automatically — a passing file is a finished solution
(`attempt-N`, and you start from a blank file); anything else is resumable
work (`wip.py`), including a `grind skip`, restored verbatim when that
problem comes back. Files that aren't known problems are never touched.

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
- Solutions + statements: `./solutions/` (override with `GRIND_SOLUTIONS`).
- Problem bank: `grind/bank.json` — extracted from neetcode.io's own published list;
  slugs/difficulties validated against LeetCode's database. Fully offline afterwards.
- Problem environments: `grind/problems.json` — statements, real signatures,
  pre-parsed example tests **plus hand-written edge cases** for all 150
  problems, built offline (`scripts/fetch_problems.py` →
  `scripts/build_problems.py`; premium problems NeetCode includes are
  hand-bundled in `scripts/premium.json`). The comparison semantics
  LeetCode's judge applies (any-order rows, in-place mutation, float
  tolerance) ship with it. Every edge case in `scripts/extras/*.json` was
  computed from — and is verified against — a heavily commented reference
  solution in `scripts/references/` (read them to learn an approach), gated
  by `scripts/edge_tool.py` / `scripts/verify_extras.py` through the same
  runner `grind done` grades with.

## Layout

```
grind/bank.json     150 problems (slug, title, difficulty, topic, roadmap order)
grind/problems.json statements + signatures + example tests + comparison semantics
grind/store.py      JSON persistence
grind/scheduler.py  FSRS wiring, readiness model, timer→rating, next-best, streaks/trends
grind/problems.py   per-problem environment: scaffold/statement rendering, test runner
grind/cli.py        commands
scripts/            one-time dataset builders (fetch → build), rebuildable offline
```
