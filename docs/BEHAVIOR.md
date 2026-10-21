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

### Problem environments — `grind/problems.json`
Bundled, offline, built once from LeetCode's published problem data by
`scripts/fetch_problems.py` + `scripts/build_problems.py` (premium problems
NeetCode includes are hand-bundled in `scripts/premium.json`). One entry per
bank slug:

| key | meaning |
|---|---|
| `markdown` | the full statement (examples + constraints), rendered to markdown |
| `python` | the real LeetCode python3 starter code, normalized to valid Python |
| `method` | the required method name for single-call problems |
| `mode` | `call` (one method call) or `ops` (design problems: constructor + operation sequence) |
| `tests` | pre-parsed examples + hand-written edge cases — see §6.1 |
| `sem` | comparison semantics the examples can't express — see §6.3 |

### State — `$GRIND_DATA_DIR/state.json` (default `~/.grind-code/state.json`)
| key | type | meaning |
|---|---|---|
| `config` | object | user + default settings (§9) |
| `cards` | {slug: FSRS card dict} | one FSRS card per seen problem |
| `logs` | list of review records | complete attempt history, chronological |
| `session` | object or null | active problem + timer start (§3) |
| `last` | slug or absent | most recently graded problem (for `grind check` fallback) |
| `graded_files` | {slug: true} | legacy flags: attempts graded before done-time archiving; consumed on resurface |
| `update` | {ts, latest} | daily version-check bookkeeping (§2 `grind update`) |

Review log record: `{slug, rating (float 1..4), solved (bool), elapsed (minutes),
new (bool — first-ever attempt), ts (aware ISO-8601 UTC), tests ("p/t" or null)}`.

Writes are atomic (temp file + rename). Missing config keys are backfilled from
defaults on load; user values are never overwritten.

### Solutions — `$GRIND_SOLUTIONS/<slug>.py` + `<slug>.md` (default `./solutions/`)
`grind next` sets up the **whole environment for the one problem**; both files
are created whenever absent and **never overwritten in place** — when a problem
is done with, its files are *filed* into `archive/<slug>/` and re-created
(statement re-rendered from the bundle, scaffold blank) when it returns:

- `<slug>.md` — the statement: header (num, title, difficulty, topic, link,
  target + phase), the full problem text with examples and constraints, and a
  note that the examples are pre-loaded into `TESTS`.
- `<slug>.py` — docstring header (num, title, difficulty, topic, URL, statement
  link, target + phase); exactly the imports the starter code references;
  `ListNode`/`TreeNode`/`Node` class definitions when the problem needs them
  (LeetCode ships these commented-out — grind emits real ones); the real
  LeetCode starter class and signature (e.g. `def twoSum(self, nums, target)`,
  design classes keep their names: `MinStack`, `LRUCache`, `Codec`); and
  `TESTS` **pre-filled from the problem's published examples plus hand-written
  edge cases** — nothing to copy from the web. Edge cases (2–4 per problem:
  empty inputs, single elements, boundaries, extremes) are bundled offline in
  `scripts/extras/*.json` and verified against reference solutions in
  `scripts/references/` via `scripts/edge_tool.py` before entering the bank.
- A problem with no bundled environment data (none today) falls back to the
  minimal scaffold: header docstring, `class Solution` with a `def solve(self)`
  stub, and an empty `TESTS` template to fill by hand.
- `archive/<slug>/` — the problem's whole history, kept forever and backed up
  like everything else: `attempt-1.py, -2, …` (graded attempts, filed by
  `grind done`), `wip.py` (an ungraded attempt parked by `grind skip`,
  restored when the problem is picked again), `statement.md` (the statement,
  re-rendered whenever the problem returns). `solutions/` itself shows only
  the active problem: at every `grind next`, stray files of *other* known
  problems are swept into their archive here (passing → `attempt-N`, else
  `wip.py`; statements → `statement.md`). Unknown files are never touched.

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
4. Sweeps `solutions/` (§1 Solutions): stray files of other known problems
   go to their archive; a parked `wip.py` for the picked problem is restored
   verbatim as the scaffold. Then the environment is set up if absent —
   scaffold **and** statement — and `session = {slug, started (UTC now),
   why, scaffold}` is recorded: the timer starts **now**.
5. Output: bold `num. title  difficulty · topic · "review"|"new problem"`,
   the LeetCode URL, the scaffold path with `target <X> · <phase>` and, when
   bundled data exists, `· statement: <slug>.md path`, and a one-line action
   hint (`solve it in your IDE, verify with grind check, then grade with grind done`).
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
   `session` cleared; `last` = slug; state saved. If the attempt file exists
   it is **archived immediately**: moved to `archive/<slug>/attempt-N.py`
   (solved or not) and the statement joins it at `statement.md`, so
   `solutions/` is clean for the next problem.
6. Output: `Title: solved|unsolved in <elapsed> (target <X> · <phase>) · rating <r>/4`,
   `next review in <interval>`, then context lines:
   - unsolved + failing gate: `failing tests — counted as unsolved; fix it and grind next brings it right back.`
   - unsolved otherwise: `look at the solution, understand it fully, then move on — it will resurface soon.`
   - solved but slow (fluency < 0.55): `solved, but a struggle — FSRS will keep this one close until it's smooth.`
   - on transition into `locked`: `target locked at your demonstrated pace — sustaining it now earns steady good ratings.` (printed once per lock)
   - `new today: <min(n,cap)>/<cap>` (display clamped to the cap) and `due now: <count>`.
   - when a file was archived: `attempt archived → <archive path>`.

### `grind check [slug] [--n N] [--all]`
Quick verification while solving — a **subset** of the suite (default: first 3
cases; `--n N` first N; `--all` everything).
1. Slug resolution order: argument → active session → `last` graded problem.
   None available → exit 1: `pass a problem id (e.g. 'two-sum'), run during an
   active session, or grade something first`.
2. Missing file → exit 1. Import failure → exit 1 with the exception. No
   solution class, no public method, or empty `TESTS` → exit 1 with a precise
   instruction (`define your solution class in <path>`; the class is normally
   `Solution`, but design problems keep their LeetCode names).
3. Runs cases (§6.4), printing one line each: `[i/n] ok|FAIL args=… -> … want …`.
4. Any failure → summary + exit 1. Empty subset (fewer cases than 3) runs what exists.

### `grind reference [slug]`
Prints the verified reference solution for `slug` — the same code whose output
computed every hand-written edge case in the bank, and that `scripts/verify_extras.py`
gates against the real runner.
1. Slug resolution: argument → active session. None available → exit 1:
   `no slug given — pass one: \`grind reference <slug>\``.
2. Missing `scripts/references/<slug>.py` → exit 1 with a hint.
3. Output: one header line, then the full file verbatim (no transformation).

### `grind extras [slug]`
Prints the hand-written edge cases that `grind done`'s full suite runs for
`slug` (the bundled examples live in the scaffold; these are the extra cases
verified against the reference solution).
1. Slug resolution: argument → active session. None available → exit 1:
   `no slug given — pass one: \`grind reference <slug>\``.
2. Missing `scripts/extras/<topic>.json` or the slug absent from it → exit 1
   with a hint.
3. Output: one header line, then each case as `case i: args=<args> want=<want>`.
   Run them interactively with `grind check <slug>`.
### `grind skip`
Drops the active session **without grading or logging**. No session → exit 1.
The ungraded attempt is not lost: if its file exists it is parked as
`archive/<slug>/wip.py` (the latest skip wins) with the statement beside it,
printing `work in progress filed → <path>`; the next time the problem is
picked, the WIP is restored exactly where it left off.

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

### `grind update`
Applies an available update — **never automatic**: it runs only when the user
types it.
1. The install must be a git checkout (the editable clone); otherwise exit 1
   with the manual command (`pip install --force-reinstall git+…`).
2. Refuses a dirty working tree (uncommitted changes to tracked files) —
   exit 1 with `commit or stash them, then retry`. Untracked files don't block.
3. `git pull --ff-only` in the install's own clone — grind supplies no fetch
   URL, so code comes from wherever the user cloned. A diverged pull fails in
   git's hands; grind exits 1 having touched nothing.
4. Re-installs editable via the running interpreter's pip
   (`python -m pip install -e .`) so the pulled code and entry points take
   effect; a pip failure exits 1 printing the exact manual command.
5. Prints `grind <version> — up to date` using the freshly pulled version.

Version check (announcement only — installs nothing): after every command, at
most once per 24h and only when config `update_check` is true, grind makes one
HTTPS GET to its own `__init__.py` on GitHub main — 3s timeout, 16KB cap,
parsed as text and never executed; nothing beyond the request is sent. A newer
version prints `update available: grind <v> (you have <v>) — run: grind update`
plus the disable hint. Every failure is silent — grind works fully offline.
The stamp lives in state `update = {ts, latest}`.

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

### 6.1 File contract — `TESTS`
`solutions/<slug>.py` defines the solution class and a module-level `TESTS`
list. `grind next` pre-fills it from the problem's published examples plus
bundled hand-written edge cases (examples first — `grind check`'s first-3
subset stays the official examples); the user can edit it freely. Two entry
shapes:

- **call mode** — `((arg, ...), expected)`: one method call. Arguments are the
  values LeetCode prints (arrays for lists/trees/graphs, scalars otherwise).
- **ops mode** — `{"ops": [...], "args": [[...], ...], "want": [...]}`: design
  problems. `ops[0]` names the class (skipped as an operation — the runner
  instantiates it), the rest are method calls with `args[i]` per op and
  `want[i]` the expected result. `want[i] = None` (constructor/void) is
  skipped. An argument of the exact string `"@prev"` is replaced by the
  previous op's return value — that's how round-trip problems
  (encode/decode, serialize/deserialize) are expressed.

### 6.2 Discovery & conversion
- **Class**: the class named by `ops[0]` in ops mode; else `Solution`; else the
  last class defined in the module. Class-dict order = definition order.
- **Method**: the dataset's recorded method name when the class defines it;
  else the **last public method** (`_`-prefixed ignored) — the scaffold's
  convention: helpers go above the required method. None → error.
- **Values**: guided by the method's type annotations — a `ListNode` arg
  becomes a linked list built from an array, `TreeNode` a tree (level-order
  with `None` holes), random-pointer `Node` a `[[val, random_index], ...]`
  list; the results convert back to the arrays LeetCode prints. A composite
  annotation like `list[ListNode | None]` (merge-k-sorted-lists) converts
  each *element* to a node chain, leaving the outer list intact. Graph
  problems (`clone-graph`) get adjacency-list conversion via the module's
  own node classes. Un-annotated methods: values pass through as-is.
- The solution file is compiled directly from source (`__pycache__` is never
  consulted — a same-size edit in the same second can't serve stale code).

### 6.3 Comparison
- Default: `got == expected`, or list/tuple loose equality. An exception thrown
  by the method counts as FAIL with the exception text as `got`.
- `sem` flags per problem (§1 problems.json):
  - `unordered` / `unordered_inner` — rows (and row contents) compared as
    multisets: any-order answers (`subsets`, `3sum`, `group-anagrams`, …).
  - `inplace: k` — the method mutates argument `k`; the final state of that
    argument is compared to `expected`.
  - `node_out_value` — the returned node is compared by `.val` (LCA).
  - `float` — numeric results within 1e-5 of the expected value pass.
  - `nqueens` / `palindromic_substring` — any *valid* answer passes (a legal
    board, a palindromic substring of the input with the expected length).
  - `nocheck: [methods]` — ops whose results aren't asserted (randomized).
  - `cycle` — the test carries LeetCode's `pos` as a trailing int arg
    (`linked-list-cycle`); the runner attaches the tail back to node `pos`
    after conversion (`-1` = no cycle; the scaffold carries a comment
    explaining the encoding).

### 6.4 Output & effects
One line per case (`[i/n] ok|FAIL` with args/ops detail), `passed/total`
summary; `grind done` prefixes `full suite: p/t passed`. The runner has no
side effects on state; `done` records the result.

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
| `update_check` | true | daily HTTPS version check (announcement only; `grind update` applies) |

## 10. Environment
| var | default | meaning |
|---|---|---|
| `GRIND_DATA_DIR` | `~/.grind-code` | state.json location |
| `GRIND_SOLUTIONS` | `./solutions` | scaffolds / solutions location |
| `EDITOR` | `vi` | editor for `--edit` / `auto_edit` |

## 11. Invariants
- The bank and the problem environments (statements, signatures, example
  tests) are static and offline: no network is ever required after install.
- The version check is the only network use: consent-gated (`update_check`),
  silent on failure, and it never installs anything — only `grind update`,
  typed by the user, ever changes the installed code.
- Nothing is ever deleted: logs only grow; solution files and statements
  only ever move deeper into `archive/` — and WIP parked there comes back.
- `solutions/` shows only the active problem; files of other problems live
  in their `archive/<slug>/` and are never lost, only filed.
- `grind skip` never writes history; `grind done` always does (even failures —
  a failed attempt is real and resets readiness).
- Grading never lies: with TESTS present, a failing suite is unsolved
  regardless of flags.
