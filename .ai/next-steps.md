# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`, `docs/backlog.md`) + the active sprint file — it does not
copy them. Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint `35_migration_merge`, PR #57 — F8/F9 fix pushed at head `bbb1a87`, awaiting a
fresh Opus re-review.** The prior REVISE (head `e22b359`) found F1's "single-writer
boundary" claim didn't hold: `tools/scaffold` and one `cli.py` read were still unpinned.
Both are now fixed and green-gated. **Next session is Opus/Architect.**

## Just done (Sonnet/Coder session, 2026-07-13)
Fixed F8 and F9 from the Opus review of PR #57 at head `e22b359`, one commit:

- **`bbb1a87` — F8, F9.**
  - **F8:** `src/loop_engine/tools/scaffold/writer.py` — pinned all three unpinned
    call sites to `encoding="utf-8"`: `write_text` (line 77), and `read_text` at both
    line 92 and line 99. Added `test_write_skeleton_claude_md_survives_non_utf8_locale_default`
    to `tests/tools/scaffold/test_writer.py` (parametrized `[None, "C"]`, mirroring F2's
    shape) — **live-verified**: reverted the writer.py fix, reran the test, `[C]` failed
    with exactly `UnicodeDecodeError: 'ascii' codec can't decode byte 0xe2...` (the bundled
    `CLAUDE.md` template's em-dashes), `[None]` still passed; restored the fix, reran —
    both pass.
  - **F9:** `src/loop_engine/cli.py:119` — pinned
    `input.read_text(encoding="utf-8") if input is not None else ""`.
- Green gate: `hatch run lint` clean, `hatch run format` clean (158 files unchanged),
  `hatch run test` — **546 passed** (544 + the two new parametrized cases).
- Pushed to the live `sprint/35-tasks-1-2` branch; PR #57 confirmed `mergeable=MERGEABLE`,
  head now `bbb1a87` (`mergeStateStatus=BLOCKED` — expected, pending the required review/checks).

## Next — Opus/Architect
**Fresh session.** `/resume` → `/code-review` PR #57 at head `bbb1a87` on
`sprint/35-tasks-1-2`. Specifically re-verify F8 and F9 are closed (see commit `bbb1a87`
above) and that no new gap of the same bug class was introduced. F10/F11 are notes only,
not required fixes. If clean: **post** the review to GitHub headed
`**Opus/Architect HITL review (automated)**` against head `bbb1a87` — this is the first
review in this round with no known blocking finding going in, so (unlike the last two)
it should actually land rather than go stale.

Then: Task 3 (pre-merge preflight) → Task 4 (open the migration PR) →
**Task 5 (the merge + settings sequence, HUMAN-ONLY)** → Task 6 (sequence the follow-on
work). **PR #55 approved the plan, not Tasks 3–5's execution — that HITL gate is still open.**

## Human actions
- **DO NOT disable `allow_merge_commit`** before the migration merge (BL-13). Last verified
  live 2026-07-13: `allow_squash_merge=true`, `allow_merge_commit=true`,
  `allow_rebase_merge=false`, `squash_merge_commit_title=PR_TITLE`,
  `delete_branch_on_merge=true`. Ordinary sprint PRs (including #57) are **SQUASH** — the
  merge-commit button exists only for the one migration PR.
- **Dependabot PRs #50–53 must NOT merge before the migration PR** (FD5) — four **major**
  action bumps that rewrite the exact `ci.yml` `uses:` SHA lines the clean merge depends on
  being identical. They get real review in Task 6, *after* the merge.
- **Carried:** delete `glunk-works/loop-engine-v3-scratch` (private, issues #1–#6); trim the
  PAT's repo list.

## Pointers
- [`sprints/35_migration_merge/sprint_plan.md`](../sprints/35_migration_merge/sprint_plan.md) —
  the approved plan. FD1–FD7 locked.
- PR #57 — Tasks 1–2, head `bbb1a87` (F8/F9 fixed this session, not yet reviewed). Prior
  heads `e7bdd7f` and `e22b359` were both reviewed REVISE and never posted (each fix moved
  the head before posting made sense).
- [`docs/backlog.md`](../docs/backlog.md) — BL-11 resolved; **BL-13 open by design** (closes in
  Task 5); BL-12/BL-14's topology gap closes with the merge itself.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — every phase closed since sprint 32.
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — five checks never run.
  **FD4: none blocks the merge**, but Task 6 gives each a scheduled home.

## Working tree
- `sprint/35-tasks-1-2` carries Tasks 1–2 plus the F8/F9 fix, pushed, PR #57 open against
  `feat/mcp-langgraph-migration`. **Live — still the branch to push any further revisions
  to.** Clean at `bbb1a87`.
- `sprint/35-migration-merge` and `sprint/35-archive-34` remain **dead** (squash-merged as
  #55/#56) — never push to either again.
- `.ai/state.json` + `.ai/archive/` are git-ignored (local mirrors); `.ai/next-steps.md` is
  tracked.
