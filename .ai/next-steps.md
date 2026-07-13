# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`, `docs/backlog.md`) + the active sprint file — it does not
copy them. Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint `35_migration_merge`, PR #57 — ninth round done: F35–F40 closed, green gate
passed.** Next session is **Opus/Architect**: fresh-session `/code-review` #4.

## Just done (Sonnet/Coder session, 2026-07-13)
Ninth round on PR #57: closed **F35–F40** from the third Opus review (posted at head
`a4527c0`, verdict REVISE), per the review's own instruction — F37 (the root cause) first,
then F35 and F36 as one edit against the shared result, not two more parallel hand-mirrored
edits.

- **F37 (blocking, root cause)** — extracted the triplicated AST mode-resolution logic
  (`mode_index = 0 if is_method else 1`, plus two copies of the write-capability check)
  into a new shared `tests/tools/_ast_open.py`: `open_call_is_method()`, `mode_node()`,
  `is_write_capable()`. Both `test_state_io_boundary.py` and `test_encoding_boundary.py`
  now import it instead of carrying their own copies.
- **F35 (blocking)** — `test_state_io_boundary.py`'s write-boundary guard now runs every
  `.open()`-shaped call through the shared `open_call_is_method()` receiver classification
  before resolving a mode, instead of treating any `.attr == "open"` as method-form Path.open
  with mode at index 0. `gzip.open('out.gz', 'wt')` outside the allowed dirs is now correctly
  flagged as a write regardless of what letters are in the filename; `gzip.open(..., 'rt')`
  is correctly not flagged.
- **F36 (blocking)** — `test_encoding_boundary.py`'s `_NON_PATH_OPEN_RECEIVERS` exclusion is
  gone. `gzip`/`bz2`/`lzma`/`codecs`/`io` now route through the shared classifier as
  index-1-mode receivers (same shape as builtin `open`), so an unencoded `gzip.open(p, 'wt')`
  or `io.open('x', 'w')` is caught instead of silently escaping the guard. Only receivers with
  no comparable mode/encoding concept at all (`os`, `shelve`, `dbm`, `webbrowser`, `tarfile`,
  `zipfile`) stay out of scope.
- **F38–F40 (non-blocking)** — `WRITE_OWNING_DIRS` renamed to `NEWLINE_PIN_SCAN_DIRS`
  (it isn't a write-owning-modules list, it's the newline-pin scan set — `agent_state` isn't
  file-write-owning per the module boundaries doc); dead `"open"` member dropped from
  `DISALLOWED_WRITE_CALLS` (the receiver-classification branch intercepts every open-shaped
  call, including bare-name `open`, before that set is ever consulted); the 79-line
  changelog docstring in `test_encoding_boundary.py` compressed to the invariant plus the
  non-obvious mode-resolution rules.

Green gate ran clean: `hatch run lint`, `hatch run format`, `hatch run test` — **553
passed**. Commit pending push — see Working tree below for the hash once pushed.

## Next — Opus/Architect
1. Fresh session, `/resume`, then `/code-review` PR #57 at the new head. Verify F35–F40
   actually hold — don't trust the commit message. In particular: confirm the shared
   `_ast_open.py` extraction didn't just move the F35/F36 bugs rather than fix them, and
   spot-check a case the review didn't name (e.g. `bz2`/`lzma` routing, which mirrors `gzip`
   but wasn't individually called out).
2. Post via `gh pr review --comment` (never `--approve`).
3. If REVISE again → hand back to Sonnet/Coder for a tenth round. If clean → tell the
   human it's ready to merge (Claude never merges/force-pushes).

## Notes only — do NOT fix without a fresh planning pass (→ backlog)
- **F2, F4, F14, F17, F23, F28** — unchanged, still correctly deferred.
- **F33 residue** — `append_memory` → `append_agent_memory` still does three full-file I/Os
  per append on a monotonically growing ledger. The docstring answer was accepted; a future
  `append_agent_memory` variant taking the already-read `existing` would remove the duplicate
  read without losing the invariant. **Not for this PR.**
- **Carried:** `architect-review` cannot distinguish "was reviewed" from "was approved" — a
  REVISE turns it green. Filed, still open, harmless while a human merges.

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
- PR #57 — Tasks 1–2, ninth round done (F35–F40 closed), awaiting review #4.
- [`docs/backlog.md`](../docs/backlog.md) — BL-11 resolved; **BL-13 open by design**.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — every phase closed since
  sprint 32.
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — five checks
  never run. **FD4: none blocks the merge**, but Task 6 gives each a scheduled home.
- Ruleset checked healthy 2026-07-13: 4 rule types, all 8 required checks on `main`.

## Working tree
- `sprint/35-tasks-1-2` carries Tasks 1–2 through the ninth-round commit (pending push),
  PR #57 open against `feat/mcp-langgraph-migration`. **Live — still the branch to
  fix/review/merge.**
- `sprint/35-migration-merge` and `sprint/35-archive-34` remain **dead** (squash-merged as
  #55/#56) — never push to either again.
- `.ai/state.json` + `.ai/archive/` are git-ignored (local mirrors); `.ai/next-steps.md` is
  tracked.
