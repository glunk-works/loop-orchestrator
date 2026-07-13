# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`, `docs/backlog.md`) + the active sprint file — it does not
copy them. Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint `35_migration_merge` is planned and APPROVED** (PR #55, squash `3ee723e`). It lands
`feat/mcp-langgraph-migration` on `main` as its one-time merge commit and closes the two-branch
topology that produced BL-12, BL-13 and BL-14 in a single week. **Next session is Sonnet/Coder**
for Tasks 1–2.

## Just done (Opus/Architect session, 2026-07-13)
- **Sprint 34 archived.** BL-11 fully closed; PRs #45, #46, #47, #48, #49, #54 all merged. Its
  final cursor is snapshotted in `.ai/archive/34_ci_supply_chain_hardening-next-steps.md`.
- **Sprint 35 planning pass** — [`sprints/35_migration_merge/sprint_plan.md`](../sprints/35_migration_merge/sprint_plan.md),
  approved by the human's merge of PR #55. The merge was **measured, not assumed**: `git merge-tree`
  is **conflict-free**, and the merged tree differs from `feat` by **exactly one file**
  (`.github/workflows/ruleset-drift.yml`, which lives only on `main`). The merged tree *is*
  `feat`'s tree — so the risk is entirely in **ordering and settings, not in code.** Also verified
  by running it, not reasoning about it: the merged workflow set passes `tests/test_ci_config.py`
  (**15 passed**) — that test **globs** `.github/workflows/*.yml`, so the merge silently widens its
  SHA-pin sweep onto a fourth file it has never seen.
- **Found while archiving: the sprint-34 handoff commit never reached `feat`.** PR #54's squash
  (`01cf067`) carries **only `docs/backlog.md`**; the handoff commit `bce312d`, which rewrote this
  file, was pushed to `sprint/34-bl14-dependabot-gap` *after* #54 had already merged — onto a
  branch the squash had already killed. It is on no integration branch. So the tracked
  `next-steps.md` on `feat` sat stale at *"sprint 34 — implementing"*, and the archive snapshot was
  taken from `bce312d` directly. **This is the squash-merged-branch-is-dead trap, one step removed:
  the branch was dead and the push still succeeded, because a dead branch is only dead by
  convention — nothing rejects the push.** `/handoff` writing a tracked file is what turns that into
  silent data loss.
- Roadmap `NEXT ACTION` updated — it had gone stale at *"none pre-selected"* since sprint 32.

## Next — Sonnet/Coder
**Sprint 35, Tasks 1 + 2, as ONE PR into `feat`.** Cut a fresh `sprint/35-*` branch from
`feat/mcp-langgraph-migration`. **Read the sprint plan first — FD1–FD7 are locked decisions; do not
re-open them.**

1. **Task 1 (`src/`)** — fix the two open `publish_artifacts` findings from PR #39's review: the
   module + function docstrings' *"publishing an unchanged state does no I/O"* claim is **false**
   (it does `exists()` + `read_text()` per artifact per stage; what it skips is the redundant
   **write**), and that `read_text()` has no explicit encoding (pass `encoding="utf-8"`, matching
   what `write_artifact` uses — **read `tools/state_io`, do not assume**). Regression test with a
   non-ASCII artifact body: publish, re-publish unchanged, assert no second write and the body is
   still byte-identical.
2. **Task 2 (docs)** — rewrite the branching protocol for the post-merge world: sprint branches cut
   from **`main`**, PRs base on **`main`** (`feat` is retired once the migration lands). Keep every
   integration-gate rule verbatim in substance (PR-is-approval, no merge, no force-push, dead
   squash-merged branches, conflicted-PR-runs-no-CI). Rewrite the one-time merge-commit exception
   into the **past tense** — a historical note explaining the merge commit on `main` — rather than
   deleting it.

The PR touches `src/`, so it needs a **fresh-session Opus architect-review** before it can merge.

**Then (Opus/human):** Task 3 pre-merge preflight → Task 4 open the migration PR → **Task 5 the
merge + settings sequence (HUMAN-ONLY)** → Task 6 sequence the follow-on work.
**PR #55 approved the plan, not its execution — Tasks 3–5 open a new HITL gate.**

## Human actions
- **DO NOT disable `allow_merge_commit`** before the migration merge (BL-13). Verified live
  2026-07-13: `allow_squash_merge=true`, `allow_merge_commit=true`, `allow_rebase_merge=false`,
  `squash_merge_commit_title=PR_TITLE`, `delete_branch_on_merge=true`. **Ordinary sprint PRs are
  SQUASH** — the merge-commit button exists only for the one migration PR, and it stays clickable on
  *every* PR until Task 5 turns it off.
- **Dependabot PRs #50–53 must NOT merge before the migration PR** (FD5) — four **major** action
  bumps that rewrite the exact `ci.yml` `uses:` SHA lines the clean merge depends on being
  identical. Merge one first and today's clean merge becomes a **conflicted PR that runs zero CI,
  silently.** They get real review in Task 6, *after* the merge.
- **Carried:** delete `glunk-works/loop-engine-v3-scratch` (private, issues #1–#6); trim the PAT's
  repo list.

## Pointers
- [`sprints/35_migration_merge/sprint_plan.md`](../sprints/35_migration_merge/sprint_plan.md) — the
  approved plan. FD1–FD7 locked.
- [`docs/backlog.md`](../docs/backlog.md) — BL-11 resolved; **BL-13 open by design** (it closes in
  Task 5); BL-12/BL-14's topology gap closes with the merge itself.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — every phase closed since sprint 32.
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — five checks never run.
  **FD4: none blocks the merge**, but Task 6 gives each a scheduled home.

## Working tree
- `sprint/35-archive-34` carries this archival. `sprint/35-migration-merge` is **dead**
  (squash-merged as #55) — never push to it again.
- `.ai/state.json` + `.ai/archive/` are git-ignored (local mirrors); **`.ai/next-steps.md` is
  tracked** — which is why a `/handoff` pushed to a dead branch loses it silently (see *Just done*).
