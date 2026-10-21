# AGENTS.md — how to work in this repo

`grind` is an FSRS-driven LeetCode fluency trainer: a Python CLI (`grind = grind.cli:main`)
that schedules daily practice over the NeetCode 150, grades attempts with a timer +
full-test-suite gate, and backs everything up invisibly.

## Ground rules

- **`docs/BEHAVIOR.md` is the authoritative behavior spec.** Any change to user-visible
  behavior MUST be reflected there (and in README where it has a section). If code and
  spec disagree, fix whichever is wrong — never let them drift.
- **Invariants (BEHAVIOR.md §11) are non-negotiable**, especially:
  - Grading/backup failures never block `grind done` or corrupt state.
  - Nothing is ever deleted — files only move deeper into `archive/`; WIP parked there
    comes back.
  - `solutions/` shows only the active problem; unknown files are never touched.
  - The version check (`grind/update.py`) is the only network use: consent-gated,
    silent on failure, never installs. Only an explicit `grind update` changes code.
- Run `pytest` after any change. Coverage gate is 95% (`pyproject.toml`); tests are
  behavior-level, through the real `cli.main` entry point.

## Commands

```bash
.venv/bin/python -m pytest -q          # full suite
.venv/bin/python -m pip install -e .   # editable install (version is dynamic!)
```

## Map

- `grind/cli.py` — all commands, presentation, archiving, backup. UI strings are part
  of the spec (tests assert on them).
- `grind/scheduler.py` — FSRS scheduling, rating, readiness, "next best" selection.
- `grind/problems.py` — test discovery/conversion/comparison for the grading gate.
- `grind/store.py` — state.json persistence (~/.grind-code); config defaults live here.
- `grind/update.py` — daily version check + `grind update` (see its module docstring
  for the security posture; keep it that narrow).
- `grind/bank.json` / `problems.json` — static problem data (offline, never fetched).
- `docs/BEHAVIOR.md` — the spec. `README.md` — user-facing doc.
- `scripts/` — data pipeline for the problem bank; not part of the runtime.

## Conventions

- Version lives ONLY in `grind/__init__.py` (`__version__`); pyproject reads it
  dynamically. The update checker fetches that same file from origin/main to compare.
- Boring and minimal: stdlib over dependencies (e.g. urllib, not requests), no
  abstractions beyond what the spec needs, comments explain *why*, not *what*.
- User data is sacred and lives OUTSIDE the repo: `~/.grind-code/state.json` (state)
  and `./solutions/` (gitignored). Never write to them in tests — use the `env`
  fixture (isolated `GRIND_DATA_DIR`/`GRIND_SOLUTIONS`, conftest.py).
- Tests: `tests/test_cli.py` exports `run(argv, capsys)` / `out(capsys)`; replicate
  `sys.exit("msg")` semantics with them. Git-using tests build real repos in
  `tmp_path` (see `remote` fixture in test_backup.py, `checkout` in test_update.py).
- `sys.exit("msg")` messages only reach stderr when uncaught — assert on
  `pytest.raises(SystemExit).value.code`, not captured output.
- New state keys: backfill with `setdefault` in `store.load()`, never overwrite user
  values; document them in BEHAVIOR.md §1.
