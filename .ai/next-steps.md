# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`, `docs/backlog.md`) + the active sprint file — it does not
copy them. Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint `35_migration_merge` — Tasks 1–2 DONE and merged** (PR #57, squashed as `a273ba0`
onto `feat/mcp-langgraph-migration`). Next up: **Tasks 3–4, Opus/Architect.**

## Just done (Opus/Architect session, 2026-07-13)
Fourth fresh-session `/code-review` of PR #57 at head `8fc8b43` — **verdict ACCEPT**,
posted via `gh pr review --comment`. The owner squash-merged it.

- **F35–F40 verified closed**, re-derived against the diff rather than taken on trust. The
  open question was whether the `tests/tools/_ast_open.py` extraction merely *relocated*
  F35/F36 behind a function boundary. It did not: `open_call_is_method()` classifies the
  receiver *before* resolving a mode, and both guards call it first and bail on `None`.
  Verified by driving the guards' internals with synthetic call shapes, not by reading them.
- **The bz2/lzma spot-check passed** — both route identically to `gzip` across all three
  guards. The generalization is real, not gzip-special-cased. F38/F39/F40 confirmed in-file.
- **Green gate reproduced independently** at `8fc8b43`: lint clean, **553 passed**.
- Ruleset re-checked healthy: 4 rule types, all 8 required checks on `main`.

## Next — Opus/Architect
1. Fresh session, `/resume`, then pick up **Tasks 3–4** from the sprint plan.
2. **Task 5 (the migration merge itself) is HUMAN-ONLY.** Task 6 is planning.
3. Work lands on `sprint/35-tasks-3-4` (already cut from `feat/mcp-langgraph-migration` at
   `a273ba0`); open the PR against `feat/mcp-langgraph-migration` — **not** `main` — until
   Task 5 executes.

## Notes only — do NOT fix without a fresh planning pass (→ backlog)
- **F41/F42 → filed as [BL-15]** in `docs/backlog.md`. The `_ast_open` classifier matches
  `open()` receivers by *bare module name*, so `import gzip as gz` defeats it and revives the
  exact F35 failure mode (`gz.open('out.gz','wt')` is a **missed write**;
  `gz.open('data.gz','rt')` is a read **false-positived** as a write). Not live in `src/`.
  The real finding is the *pattern*: F30 → F35 → F41 is one defect recurring because each
  round enumerated another name into a set instead of removing the assumption. Fix is to bind
  `ast.Import`/`ast.ImportFrom` aliases instead of guessing. F42 (gzip/bz2/lzma default to
  **binary**, not text, so a bare `gzip.open(p)` is misflagged) is a one-liner in the same
  file — fix both together.
- **F2, F4, F14, F17, F23, F28** — unchanged, still correctly deferred.
- **F33 residue** — `append_agent_memory` still does three full-file I/Os per append. The
  docstring answer was accepted. Not a blocker.
- **Carried:** `architect-review` cannot distinguish "was reviewed" from "was approved" — a
  REVISE turns it green. Filed, still open, harmless while a human merges.

## Human actions
- **DO NOT disable `allow_merge_commit`** before the migration merge (BL-13) — the
  merge-commit button exists only for the migration PR (Task 5). Ordinary sprint PRs squash.
- **Dependabot PRs #50–53 must NOT merge before the migration PR** (FD5) — four **major**
  action bumps that rewrite the exact `ci.yml` `uses:` SHA lines the clean merge depends on
  being identical. Real review in Task 6, after the merge.
- **Carried:** delete `glunk-works/loop-engine-v3-scratch` (private, issues #1–#6); trim the
  PAT's repo list.

## Pointers
- [`sprints/35_migration_merge/sprint_plan.md`](../sprints/35_migration_merge/sprint_plan.md) —
  the approved plan. FD1–FD7 locked. **PR #55 approved the plan, not Tasks 3–5's execution.**
- PR #57 — Tasks 1–2, **MERGED** (squashed as `a273ba0`).
- [`docs/backlog.md`](../docs/backlog.md) — BL-11 resolved; **BL-13 open by design**.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — every phase closed since
  sprint 32.
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — five checks
  never run. **FD4: none blocks the merge**, but Task 6 gives each a scheduled home.
- Ruleset checked healthy 2026-07-13: 4 rule types, all 8 required checks on `main`.

## Working tree
- `sprint/35-tasks-3-4` — **live**, cut from `feat/mcp-langgraph-migration` at `a273ba0`.
  Carries this cursor commit; Tasks 3–4 land here.
- `sprint/35-tasks-1-2`, `sprint/35-migration-merge`, `sprint/35-archive-34` are all **dead**
  (squash-merged as #57/#55/#56) — never push to any of them again.
- `.ai/state.json` + `.ai/archive/` are git-ignored (local mirrors); `.ai/next-steps.md` is
  tracked.
