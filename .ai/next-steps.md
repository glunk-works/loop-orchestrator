# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`, `docs/backlog.md`) + the active sprint file — it does not
copy them. Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint `35_migration_merge`, PR #57 — F29–F34 closed at head `783e827`, awaiting review.**
Next session is **Opus/Architect**: fresh-session `/code-review`, post, decide verdict.

## Just done (Sonnet/Coder session, 2026-07-13)
Eighth round on PR #57: closed **F29–F34** from the second Opus follow-up review
(posted at head `fb93715`, verdict REVISE).

- **F29 (blocking)** — `test_state_io_boundary.py`'s `_direct_write_calls` now detects
  method-form `.open()`. Added a write-capability check (`_is_write_capable_open`): no
  mode arg at all → read, unflagged; an unresolvable mode → stays in scope; a resolved
  `w`/`a`/`x`/`+` mode → flagged. Applied symmetrically to the bare-name `open()` branch
  too, closing the inconsistency the review named (a bare `open('x','r')` was
  unconditionally flagged while `path.open('w')` wasn't).
- **F30 (blocking)** — `test_encoding_boundary.py` added `_is_path_open()`, which
  excludes known non-Path receivers (`gzip`, `bz2`, `lzma`, `io`, `codecs`, `shelve`,
  `tarfile`, `zipfile`, `dbm`, `webbrowser`, `os`) from the method-form `.open()` branch,
  so `gzip.open('blob.gz','wt')` etc. can no longer have their filename misread as a mode.
- **F31** — `WRITE_OWNING_DIRS` now includes `tools/agent_state` (the module this PR
  gave its first `.open()` handle to); scanning it today finds nothing (the call is a
  read), but a future write-mode open there is now covered.
- **F32** — the `utf8_mode` skipif in `test_artifact_store.py` and
  `scaffold/test_writer.py` now scopes to only the `'C'` `pytest.param`, so the
  locale-independent `None` case can't silently vanish under PEP 686 (Python 3.15+).
- **F33** — docstring added to `agent_state/store.py::append_memory` explaining the
  append-only prefix check is tautological for its only caller today (its real coverage
  is a TOCTOU race, not a mis-rendering caller) — answered as a docstring, not a refactor,
  per the prior session's judgment call.
- **F34** — `_is_write_capable_mode` now takes the call node directly and distinguishes
  "no mode argument" (a read) from "an unresolvable mode" (stays in scope, F21's
  conservatism), instead of collapsing both to the same `None`.

Green gate ran clean: `hatch run lint`, `hatch run format`, `hatch run test` — **553
passed**. Commit `783e827`, pushed to `sprint/35-tasks-1-2`.

## Next — Opus/Architect
1. Fresh session, `/resume`, then `/code-review` PR #57 at head `783e827`. Verify F29–F34
   actually hold — don't trust the commit message.
2. Post via `gh pr review --comment` (never `--approve`).
3. If REVISE again → hand back to Sonnet/Coder for a ninth round. If clean → tell the
   human it's ready to merge (Claude never merges/force-pushes).

## Notes only — do NOT fix without a fresh planning pass (→ backlog)
- **F2, F4, F14, F17, F23** — unchanged, still correctly deferred.
- **F28** — optional, verified moot; no backlog entry needed.
- **Carried:** `architect-review` cannot distinguish "was reviewed" from "was approved"
  (a REVISE turns it green) — filed, still open, harmless while a human merges.

## Human actions
- **DO NOT disable `allow_merge_commit`** before the migration merge (BL-13). Ordinary
  sprint PRs (including #57) are **SQUASH** — the merge-commit button exists only for
  the migration PR.
- **Dependabot PRs #50–53 must NOT merge before the migration PR** (FD5) — four **major**
  action bumps that rewrite the exact `ci.yml` `uses:` SHA lines the clean merge depends
  on being identical. Real review in Task 6, after the merge.
- **Carried:** delete `glunk-works/loop-engine-v3-scratch` (private, issues #1–#6); trim
  the PAT's repo list.

## Pointers
- [`sprints/35_migration_merge/sprint_plan.md`](../sprints/35_migration_merge/sprint_plan.md) —
  the approved plan. FD1–FD7 locked. **PR #55 approved the plan, not Tasks 3–5's execution.**
- PR #57 — Tasks 1–2, eighth round (F29–F34 closed). Awaiting fresh-session review at
  head `783e827`.
- [`docs/backlog.md`](../docs/backlog.md) — BL-11 resolved; **BL-13 open by design**.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — every phase closed since
  sprint 32.
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — five checks
  never run. **FD4: none blocks the merge**, but Task 6 gives each a scheduled home.
- Ruleset checked healthy 2026-07-13: 4 rule types, all 8 required checks on `main`.

## Working tree
- `sprint/35-tasks-1-2` carries Tasks 1–2 through `783e827`, pushed, PR #57 open against
  `feat/mcp-langgraph-migration`. **Live — still the branch to fix/review/merge.**
- `sprint/35-migration-merge` and `sprint/35-archive-34` remain **dead** (squash-merged as
  #55/#56) — never push to either again.
- `.ai/state.json` + `.ai/archive/` are git-ignored (local mirrors); `.ai/next-steps.md` is
  tracked.
