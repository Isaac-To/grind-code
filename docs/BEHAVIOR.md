# grind — Complete Behavior Specification

Every behavior of the tool, normatively. The README is the quick-start; this is
the reference. Anything not stated here is a bug.

---

## 1. Data model

### Problem bank — `grind/bank.json`
- Exactly **150 problems**, the NeetCode 150 list, extracted from neetcode.io's
  own published data and validated against LeetCode's database (slugs resolve,
  difficulties match).
- Each entry: `slug` (LeetCode URL id), `num` (current LeetCode number), `title`,
  `difficulty` ∈ {Easy, Medium, Hard}, `topic`.
- **18 topics**, in NeetCode roadmap order: Arrays & Hashing, Two Pointers,
  Sliding Window, Stack, Binary Search, Linked List, Trees, Heap /
  Priority Queue, Backtracking, Tries, Graphs, Advanced Graphs, 1-D DP,
  2-D DP, Greedy, Intervals, Math & Geometry, Bit Manipulation.
- Problems appear in bank order = NeetCode's curated within-topic order
  (roughly Easy → Hard). This order *is* the introduction order within a topic.

### State — `$GRIND_DATA_DIR/state.json` (default `~/.grind-code/state.json`)
| key | type | meaning |
|---|---|---|
| `config` | object | user + default settings (§9) |
| `cards` | {slug: FSRS card dict} | one FSRS card per seen problem |
| `logs` | list of review records | complete attempt history, chronological |
| `session` | object or null | active problem + timer start (§3) |
| `last` | slug or absent | most recently graded problem (for `grind check` fallback) |

Review log record: `{slug, rating (float 1..4), solved (bool), elapsed (minutes),
new (bool — first-ever attempt), ts (aware ISO-8601 UTC), tests ("p/t" or null)}`.

Writes are atomic (temp file + rename). Missing config keys are backfilled from
defaults on load; user values are never overwritten.

### Solutions — `$GRIND_SOLUTIONS/<slug>.py` (default `./solutions/`)
A scaffold is created on first `grind next` for a problem and **never
overwritten**. Contents: docstring (number, title, difficulty, topic, URL,
current target + phase), a `class Solution` stub, and a `TESTS` template.

---

## 2. Commands

Exit codes: **0** success, **1** any user/data error or failing test suite.

### `grind` (bare) — equivalent to `grind next`.

### `grind next`
Presents the single best problem and starts the session timer.
1. If a session is active: prints it + elapsed, and does nothing else.
2. On the very first presentation ever (`seen_intro` unset in state), prints a
   one-time welcome teaching the daily loop (next / check / done), then sets
   the flag — never shown again.
3. Picks via the selection algorithm (§7). If nothing is pickable:
   `All caught up — nothing due right now.` plus `Next review: <title> in <interval>`
   if any card exists with a future due date.
4. Creates the scaffold if absent, records `session = {slug, started (UTC now),
   why, scaffold}` — the timer starts **now**.
5. Output: bold `num. title  difficulty · topic · "review"|"new problem"`,
   the LeetCode URL, the scaffold path with `target <X> · <phase>`, and a
   one-line action hint (`solve it in your IDE, verify with grind check, then
   grade with grind done`).
6. `--web` or config `auto_web=true`: opens the problem page in the browser.
   `--edit` or config `auto_edit=true`: opens the scaffold in `$EDITOR` (vi if
   unset) and blocks until the editor exits.

### `grind done`
Stops the timer and grades. Order of operations:
1. Requires an active session; else exits 1: `No active session. Start one with: grind next`.
2. Elapsed = wall clock from `started` until now (test execution included);
   `--mins N` overrides it.
3. `--rating X` must satisfy 1 ≤ X ≤ 4, validated *before anything else runs*;
   else exits 1: `rating override must be within 1..4`.
4. **Solved determination** (ground truth, in order):
   - Solution file exists but fails to import → **unsolved**, error printed.
   - Solution file has `TESTS` → the **entire list** runs (§6.4).
     All pass → solved. Any failure → unsolved. `--solved`/`--fail` are ignored
     in this case (a note is printed when they disagree with the result):
     `note: --solved/--fail overridden by TESTS (tests are authoritative)`.
   - No TESTS (or no file) → `--solved` / `--fail` decide; with neither, the
     user is prompted `Solved it? [y/n]` (repeats on other input; Ctrl-D/Ctrl-C
     exits 1 with *session kept*: `no answer — session kept, retry with: grind done`).
5. Rating: `--rating` if given, else derived from timer (§5.3). Applied to FSRS
   (§5.4). A log record is appended (`tests` = `"passed/total"` when the gate ran);
   `session` cleared; `last` = slug; state saved.
6. Output: `Title: solved|unsolved in <elapsed> (target <X> · <phase>) · rating <r>/4`,
   `next review in <interval>`, then context lines:
   - unsolved + failing gate: `failing tests — counted as unsolved; fix it and grind next brings it right back.`
   - unsolved otherwise: `look at the solution, understand it fully, then move on — it will resurface soon.`
   - solved but slow (fluency < 0.55): `solved, but a struggle — FSRS will keep this one close until it's smooth.`
   - on transition into `locked`: `target locked at your demonstrated pace — sustaining it now earns steady good ratings.` (printed once per lock)
   - `new today: <min(n,cap)>/<cap>` (display clamped to the cap) and `due now: <count>`.

### `grind check [slug] [--n N] [--all]`
Quick verification while solving — a **subset** of the suite (default: first 3
cases; `--n N` first N; `--all` everything).
1. Slug resolution order: argument → active session → `last` graded problem.
   None available → exit 1: `pass a problem id (e.g. 'two-sum'), run during an
   active session, or grade something first`.
2. Missing file → exit 1. Import failure → exit 1 with the exception. Missing
   `Solution` class, no public method, or empty `TESTS` → exit 1 with a
   precise instruction.
3. Runs cases (§6.4), printing one line each: `[i/n] ok|FAIL args=… -> … want …`.
4. Any failure → summary + exit 1. Empty subset (fewer cases than 3) runs what exists.

### `grind skip`
Drops the active session **without grading or logging**. No session → exit 1.

### `grind status`
One-screen snapshot: `seen/150 · due · new today (clamped) · streak cur (best) ·
proven/150`, then `interview readiness: X% (goal 80%)` (with ✓ when ≥ goal),
`least ready: <3 lowest topics>`, and the active session if any.

### `grind topics`
Per-topic readiness table sorted least-ready first: `topic  seen a/b  ready X%
[bar of █]`, footer explaining readiness, and the overall number vs goal.

### `grind stats`
- `streak: <cur>d current (best <best>d)`
- `solved: <attempts> attempts · <distinct> distinct problems · <proven> proven`
- `interview readiness: X% (goal 80%)`
- trends (only with ≥4 solved attempts): rating, solve rate, pace
  (`X.XXx of target time`) each as `first half -> recent half` of the
  chronological log;
- `last 14 days` activity sparkline (`·` for empty days, ▁▂▃▄▅▆▇█ scaled to the
  peak) and the peak count.

### `grind config [key=value]`
No argument: prints all keys. With `key=value`: the value is type-validated
against the key's default (bool keys take `true`/`false`; numeric keys take
numbers) — mismatches exit 1 with a clear message and **never** modify state.
Unknown key → exit 1. Persisted immediately.

### `grind backup [--remote URL]` / `grind restore [url] [--force]`
Backup is **invisible and always-on**:
- **First boot** (the one-time welcome): grind asks where to back up — the git
  url of your backup repo. Any git remote works: GitHub, GitLab, a self-hosted
  or bare SSH repo, even a local path like `/mnt/nas/grind.git`. Bare words
  are rejected with a hint (they aren't a usable remote). Enter = local-only.
  Grind never creates the repo — you make it on your host of choice. If the
  given repo **already holds a grind backup** (a returning user on a new
  machine), it is pulled immediately and progress continues where it left off.
- After **every `grind done`**, progress (`state.json`) and all solutions are
  committed to a local history git repo at `$GRIND_DATA_DIR/repo/` — offline,
  instant, never announced.
- Cloud push happens automatically whenever `backup_remote` is configured —
  pushed even when nothing new was committed. Authentication is entirely the
  user's own git credentials (SSH keys / credential helper); grind never
  handles tokens and has no `gh` dependency. Pushing to a repo that doesn't
  exist yet surfaces one line with a create-it hint.
- Success prints **nothing**. Failures print one `backup: …` line and never
  block grading or recording the attempt. With no remote configured, a
  one-time nudge (`backup: local only — …`) prints once, never again.
- `grind backup` forces a backup now (prompts for the url if never answered);
  `--remote URL` also saves the URL as `backup_remote`.
- `grind restore` pulls the backup onto the current machine: url argument →
  `backup_remote` → prompt. Refuses to overwrite existing local state unless
  `--force`; restores state and solutions; `__pycache__`/`*.pyc` are never
  backed up.



---

## 3. Timer semantics
- Wall clock from `grind next` to `grind done`, persisted in the session — the
  terminal may close in between; `done` works from a fresh one.
- Test execution time is part of elapsed (seconds; negligible).
- `--mins N` is the honest override after a break. The timer never stops on its own.

## 4. Readiness model — "interview ready"
- **Problem readiness** = `0` if never seen; `0` if the *last attempt* was
  unsolved (remembered-but-unproducible doesn't count); otherwise the FSRS
  recall probability *right now* (decays until the next review).
- **Topic readiness** = mean over *every* bank problem in the topic (unseen = 0).
- **Overall readiness** = mean over all 150 problems. Interview-ready bar:
  **80%** (`READY_GOAL`).
- `proven` (status/stats) = problems whose last attempt was solved, independent
  of recall decay.

## 5. Grading — the floating system

### 5.1 Personal target (`target_info`)
Constants: floor factor 0.6, convergence window 5 solved attempts (worst one
dropped), band 1.5, lock grace 1.1, solve floor 2.2.

Phases (shown in every prompt as `target X · phase`):
- **prior** — fewer than 2 solved attempts: the difficulty prior
  (Easy 15 / Medium 30 / Hard 45 min; community practice-time data).
- **calibrating** — target = median of the last 6 solved attempts, floored at
  0.6 × prior. The bar follows your pace while it moves.
- **locked** — when the last 5 solved attempts, after dropping the single worst
  one, satisfy `slowest ≤ 1.5 × fastest`: that's your demonstrated peak. Target
  locks at `median(core) × 1.1` (still ≥ floor) and stops chasing speed.
  - A single bad day cannot unlock it (the outlier is dropped).
  - Persistent drift (enough slow attempts to break the band) returns to
    **calibrating**, where the median rises toward the new pace — recalibration,
    not punishment — and re-locks once the new pace stabilizes.
- Unsolved attempts never move the target.

### 5.2 Fluency
`fluency = 2 / (2 + elapsed/target)` ∈ [0,1]: 1.0 instant, ~0.67 at target,
decaying smoothly past it; 0 if unsolved.

### 5.3 Rating
`rating = max(2.2, min(4.0, 1 + 3 × fluency))` for solved attempts — a produced,
working solution never rates below 2.2 ("hard") no matter how slow; `1.0` when
unsolved. At exactly target time the rating is 3.0 ("good"). `--rating` bypasses
the timer entirely (still gated to [1,4]).

### 5.4 FSRS application
Engine: [py-fsrs](https://github.com/open-spaced-repetition/py-fsrs) ≥ 6 (the
algorithm inside modern Anki), desired retention 0.9 (config `retention_target`),
interval fuzzing on.
- Integer/whole ratings apply directly.
- Fractional ratings: both adjacent integer ratings are computed; if both
  outcomes are in the FSRS *Review* state, the result card is the linear
  interpolation (stability, difficulty, and due datetime) — intervals vary
  continuously with your speed.
- Inside learning steps (fixed-minute intervals) the fraction rounds (≥ .5 up).
- First-ever attempt marks the log `new: true`; that's what consumes daily quota.

## 6. Test running (check / done gate)

### 6.1 File contract
`solutions/<slug>.py` must define `class Solution` and a module-level `TESTS`
list of `(args_tuple, expected)` pairs.

### 6.2 Method discovery
The callable method is the **last public method defined in `Solution`**
(`_`-prefixed names and dunders ignored; class-dict order = definition order).
Convention: helpers go above the required method. No public method → error.

### 6.3 Comparison
`got == expected`, or list/tuple loose equality (`list(got) == list(expected)`).
An exception thrown by the method counts as FAIL with the exception text as `got`.

### 6.4 Output & effects
One line per case, `passed/total` summary; `grind done` prefixes `full suite:
p/t passed`. The runner has no side effects on state; `done` records the result.

## 7. "Next best" selection
1. **Due reviews first** (FSRS due ≤ now), most-overdue first.
2. Otherwise, one **new problem**, if today's new count < `daily_new`:
   from the topic with the **lowest readiness** among topics with unseen
   problems; ties → fewer problems seen; still tied → roadmap order (so a cold
   start walks the roadmap, interleaving as topics strengthen). Within the
   topic: first unseen problem in bank (curated) order.
3. Otherwise: nothing (caught up; upcoming review is reported).

## 8. Stats definitions
- **Activity day**: local calendar date of a log's timestamp.
- **Streak**: consecutive activity days; current survives if the last activity
  was today or yesterday; best is the longest run ever.
- **Trends** (≥4 solved attempts): the chronological log is split in half;
  rating = mean over solved attempts; solve rate = solved/total per half;
  pace = median of `elapsed / effective_target` per solved attempt.

## 9. Configuration (`grind config`)
| key | default | meaning |
|---|---|---|
| `daily_new` | 5 | max new problems introduced per local day |
| `targets` | {Easy: 15, Medium: 30, Hard: 45} | practice-time priors, minutes |
| `retention_target` | 0.9 | FSRS desired retention |
| `auto_web` | false | `next` always opens the problem page |
| `auto_edit` | false | `next` always opens the scaffold in `$EDITOR` |
| `backup_remote` | "" | git url of your backup repo (any host; asked on first boot) |

## 10. Environment
| var | default | meaning |
|---|---|---|
| `GRIND_DATA_DIR` | `~/.grind-code` | state.json location |
| `GRIND_SOLUTIONS` | `./solutions` | scaffolds / solutions location |
| `EDITOR` | `vi` | editor for `--edit` / `auto_edit` |

## 11. Invariants
- The bank is static and offline: no network is ever required after install.
- Nothing is ever deleted: logs only grow; scaffolds are only created.
- `grind skip` never writes history; `grind done` always does (even failures —
  a failed attempt is real and resets readiness).
- Grading never lies: with TESTS present, a failing suite is unsolved
  regardless of flags.
