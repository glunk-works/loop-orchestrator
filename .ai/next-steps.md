# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`, `docs/backlog.md`) + the active sprint file — it does not
copy them. Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint `35_migration_merge`, Tasks 1–2 implemented and pushed as PR #57** (`sprint/35-tasks-1-2`
→ `feat/mcp-langgraph-migration`). Local green gate: 543 tests passed, lint clean, format clean.
**Next session is Opus/Architect** — the PR touches `src/`, so it needs a fresh-session
`architect-review` before the human can merge it.

## Just done (Sonnet/Coder session, 2026-07-13)
- **Task 1** — `tools/artifact_store.py`'s `publish_artifacts` docstrings (module + function)
  corrected: they claimed publishing an unchanged state does no I/O, which is false — it
  `exists()` + `read_text()`s every artifact on every stage and only skips the redundant
  **write**. Added explicit `encoding="utf-8"` to the read-back (checked `tools/state_io` first —
  `write_artifact` uses the same default-text-encoding path, so no mismatch). Added a regression
  test: a non-ASCII artifact body is published, re-published unchanged, asserted no second write
  and byte-identical on disk. These were the two open findings from PR #39's review.
- **Task 2** — Rewrote the branching protocol in `CLAUDE.md` and `.ai/context/workflow.md` for the
  post-merge world: sprint branches cut from `main`, PRs base on `main`. Every integration-gate
  rule (PR-is-approval, no merge, no force-push, dead squash-merged branches, conflicted-PR-no-CI)
  survives verbatim in substance. The one-time merge-commit exception is now a **past-tense
  historical note** in `workflow.md` rather than deleted. The three skill files
  (`resume`/`handoff`/`archive-sprint`) needed no edits — none hard-codes the branch name.
- Both changes landed in one commit (`df28d60`), pushed as **PR #57** into `feat/mcp-langgraph-migration`.
  `grep -rn "mcp-langgraph-migration"` over `CLAUDE.md`/`workflow.md` now returns only the
  intentional historical-note references.

## Next — Opus/Architect
**Fresh session.** `/resume` → `/code-review` PR #57's diff → post the
`**Opus/Architect HITL review (automated)**` with the fresh-session attestation via
`gh pr review --comment` against its current head commit (never `--approve`). Scope: does Task 1's
fix accurately describe the code and match `write_artifact`'s encoding; does Task 2 preserve every
integration-gate rule in substance and correctly relegate the merge-commit exception to the past
tense. Once posted and the human merges #57, **`feat` is frozen (FD3)** — nothing should push to it
again until Task 3's preflight re-opens it immediately before the migration PR is cut.

**Then (Opus/human):** Task 3 pre-merge preflight → Task 4 open the migration PR → **Task 5 the
merge + settings sequence (HUMAN-ONLY)** → Task 6 sequence the follow-on work.
**PR #55 approved the plan, not Tasks 3–5's execution — that HITL gate is still open.**

## Human actions
- **DO NOT disable `allow_merge_commit`** before the migration merge (BL-13). Last verified live
  2026-07-13: `allow_squash_merge=true`, `allow_merge_commit=true`, `allow_rebase_merge=false`,
  `squash_merge_commit_title=PR_TITLE`, `delete_branch_on_merge=true`. Ordinary sprint PRs
  (including #57) are **SQUASH** — the merge-commit button exists only for the one migration PR.
- **Dependabot PRs #50–53 must NOT merge before the migration PR** (FD5) — four **major** action
  bumps that rewrite the exact `ci.yml` `uses:` SHA lines the clean merge depends on being
  identical. They get real review in Task 6, *after* the merge.
- **Carried:** delete `glunk-works/loop-engine-v3-scratch` (private, issues #1–#6); trim the PAT's
  repo list.

## Pointers
- [`sprints/35_migration_merge/sprint_plan.md`](../sprints/35_migration_merge/sprint_plan.md) — the
  approved plan. FD1–FD7 locked.
- PR #57 — Tasks 1–2, awaiting Opus HITL review.
- [`docs/backlog.md`](../docs/backlog.md) — BL-11 resolved; **BL-13 open by design** (closes in
  Task 5); BL-12/BL-14's topology gap closes with the merge itself.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — every phase closed since sprint 32.
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — five checks never run.
  **FD4: none blocks the merge**, but Task 6 gives each a scheduled home.

## Working tree
- `sprint/35-tasks-1-2` carries Tasks 1–2, pushed, PR #57 open against `feat/mcp-langgraph-migration`.
  Tree is clean at `df28d60`.
- `sprint/35-migration-merge` and `sprint/35-archive-34` remain **dead** (squash-merged as #55/#56)
  — never push to either again.
- `.ai/state.json` + `.ai/archive/` are git-ignored (local mirrors); `.ai/next-steps.md` is tracked.
