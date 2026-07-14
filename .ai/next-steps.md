# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`, `docs/backlog.md`) + the active sprint file — it does not
copy them. Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint `35_migration_merge` — Tasks 3–4 DONE.** The migration PR (**#58**) is open and sits at
**seven of eight green**. Status: **`awaiting_hitl_review`**.

## Just done (Opus/Architect session, 2026-07-13/14)
- **Task 3 preflight PASSED, twice** — re-run after the gate fix at `main`=`3e7116f`,
  `feat`=`b669482`: `merge-tree` exit 0, merged tree `4aad78e`, delta vs `feat` is **exactly**
  `.github/workflows/ruleset-drift.yml` (+70). Dependabot #50–53 all still OPEN. **FD1 holds.**
- **Task 4: PR #58 opened** — base `main`, head `feat/mcp-langgraph-migration` @ `b669482`,
  113 commits, 197 files. Body carries the observed preflight + the **never-squash** instruction.
- **Found and fixed a live gate defect (#59 → `feat`, #60 → `main`, both merged).**
  `architect-review` was **exempting itself on large PRs**: its `src/`-detection piped a
  paginating `gh` into `grep -q`; grep exits at its first match, `gh` dies of SIGPIPE (141),
  `pipefail` promotes 141 to the pipeline's status, and `if !` reads that as *"no src/ changes"* →
  `exit 0`, **green**. It reported "No src/ changes" over **66 changed `src/` files** on #58.
  It failed **green, not `skipped`**, and only on diffs large enough to keep `gh` paginating — so
  the gate **silently weakened as diffs grew** and was least trustworthy on the largest PRs.
  Fix had to be **byte-identical on both branches** (the file is absent at the merge base and was
  added independently on each side — patching one alone = add/add conflict = **zero CI, silently**).
  **Proven fixed by #58 itself:** its `architect-review` went from green-with-no-review to
  correctly **RED**. Pinned by a structural test that fails against the pre-fix workflow.
- **Filed [BL-16]** (`7875c79`) — the finding that outlives the bug: `ruleset-drift.yml` verifies a
  gate is *required*, never that it *works*. An inert gate passes every alarm **because** it is inert.

## Next — Opus/Architect, FRESH SESSION
1. `/resume`, then `/code-review` **PR #58** and post it:
   `gh pr review 58 --comment --body-file <f>` — **never `--approve`**.
2. **Scope it per FD7:** an **integration** review of the merged tree's coherence (does the merge
   produce the predicted workflow set; is `ci.yml` the post-sprint-33 version; do the four
   workflows co-exist; is `main`'s topology correct). **Explicitly decline** to re-review the 113
   commits — each already carried its own architect-review. A review claiming otherwise is a lie of
   exactly the kind these gates exist to prevent.
3. Must carry the `**Opus/Architect HITL review (automated)**` header + the fresh-session
   attestation, and bind to head **`b669482`**. That turns the 8th check green.
4. **Task 5 (the merge + the `allow_merge_commit` sequence) is HUMAN-ONLY.** Task 6 is planning.

> **This session cannot post that review** — it authored the diff under review (#59/#60). That is
> precisely what the attestation forbids.

## Freeze / branch discipline
- **`feat/mcp-langgraph-migration` is FROZEN at `b669482`** (FD3). Any push moves #58's head and
  invalidates the review binding. `main` is at `3e7116f`.
- **`sprint/35-tasks-3-4`** holds 3 docs commits (cursor, BL-15, BL-16), **not yet PR'd**. Do **not**
  merge it into `feat` before the review is posted — it lands on `main` after the merge (Task 6).
- Dead (squash-merged), never push: `sprint/35-tasks-1-2`, `sprint/35-hitl-gate-fix`,
  `sprint/35-hitl-gate-fix-main`, `sprint/35-migration-merge`, `sprint/35-archive-34`.

## Gotcha worth remembering
When #59's merge moved `feat`, GitHub **did not fire `synchronize`** on #58 — `pr-title` and
`architect-review` had **no check-run at all** at the new head, and the PR read `blocked` (it fails
safe, not mergeable). Recovery is **close + reopen** (`reopened` is in both workflows' triggers) —
never an empty commit, never a force-push. **"Checks vanished" looks nothing like "checks failed."**

## Human actions
- **DO NOT disable `allow_merge_commit`** before the migration merge (BL-13).
- **Dependabot #50–53 must NOT merge before #58** (FD5) — they rewrite the exact `ci.yml` `uses:`
  lines whose byte-identity makes the merge conflict-free.
- **Carried:** delete `glunk-works/loop-engine-v3-scratch`; trim the PAT's repo list.

## Pointers
- [`sprints/35_migration_merge/sprint_plan.md`](../sprints/35_migration_merge/sprint_plan.md) — FD1–FD7 locked.
- PR **#58** — the migration PR (open, 7/8 green). PRs #59/#60 — the gate fix, **merged**.
- [`docs/backlog.md`](../docs/backlog.md) — **BL-16 new**; BL-15 open; BL-13 open by design.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — every phase closed since sprint 32.
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — five checks never run
  (**FD4: none blocks the merge**; Task 6 homes them).
- Ruleset checked healthy 2026-07-13: 4 rule types, all 8 required checks on `main`.
