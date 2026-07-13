# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`, `docs/backlog.md`) + the active sprint file — it does not
copy them. Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint `34_ci_supply_chain_hardening` is done.** BL-11 is fully closed. The next unit is a
**new Opus planning task**, added by the human: scope the `feat/mcp-langgraph-migration` → `main`
merge. **Next session is Opus/Architect.**

## Just done (Sonnet/Coder session, 2026-07-13)
- **Sprint 34 (BL-11) shipped in full.** Tasks 1, 2, 3, 5, 6 via PR #45 (squash `bea926e`+`77c7fec`
  into `feat/mcp-langgraph-migration`). Task 4 (`ruleset-drift.yml`) via PR #47 into `main`, and
  **both post-merge acceptance criteria were live-verified, not assumed**: a manual
  `workflow_dispatch` run confirmed `GITHUB_TOKEN` (only `contents: read` — no scope escalation
  needed) actually read the effective-rules endpoint and saw all 8 checks; a second dispatch on a
  throwaway branch with a fake 9th check name confirmed the workflow goes red for the right reason
  (that branch was deleted, never merged).
- **Three follow-on findings surfaced live and resolved**, all in `docs/backlog.md`:
  - **BL-12** — before opening Task 4's PR, checked `main` live rather than assuming it mirrored
    `feat/mcp-langgraph-migration`. It was **106 commits behind** and missing `pr-title.yml` +
    `hitl-review.yml` entirely, so any PR against `main` would have hung forever on 2 of its 8
    required checks. Backported both files verbatim (PR #46) — self-referentially proved correct
    when both new checks resolved on the PR that introduced them.
  - **BL-13** — the repo owner caught this before it was acted on: sprint 34's human-actions list
    said to disable `allow_merge_commit` repo-wide, but `.ai/context/workflow.md` documents a
    one-time exception — the migration's eventual landing on `main` is a **merge commit**,
    deliberately never squashed. Corrected in `docs/backlog.md` and the sprint plan in place (PR
    #48). `allow_rebase_merge: false` is set; `allow_merge_commit` stays enabled until the
    migration merge itself.
  - **BL-14** — found while answering a question about how action-version updates would work
    going forward: Dependabot reads `dependabot.yml` **only from the default branch**, so Task 1's
    SHA pins and Task 2's `github-actions` entry were inert on `main` until backported (PR #49).
    Confirmed live: the moment #49 merged, Dependabot immediately opened **PRs #50–53**, bumping
    all four pinned actions — all **major-version** jumps, flagged for real human review rather
    than auto-merge.
  - BL-12 and BL-14 are named in the backlog as **one repeating pattern**: anything that must live
    on the default branch to function (Dependabot config, scheduled workflows, branch-protection
    settings) is silently inert on `feat/mcp-langgraph-migration` until it reaches `main`.
- PR #54 (docs-only, logs the BL-14 finding) is **green, awaiting merge** — no architect-review
  needed (no `src/` touched).

## Next — Opus/Architect
**New planning task, not yet a numbered sprint.** Scope what must happen before
`feat/mcp-langgraph-migration` merges into `main` as its one-time merge-commit landing, versus
what can be safely deferred to post-merge. This is a **planning pass** — produce a plan/checklist
and HITL-gate it with the human; do not start executing the merge unilaterally.

Known inputs to weigh:
1. **BL-13's ordering** — `allow_merge_commit` must be enabled for that one PR, then disabled
   again immediately after.
2. **`sprints/DEFERRED_VERIFICATION.md`** — five checks (§1, §5, §6, §7, §8) have never been run.
   Decide which, if any, are must-run-before-merge vs. safe to leave for after.
3. **Two still-open, non-blocking findings from PR #39's review** — `publish_artifacts`' "does no
   I/O" docstring is false (it reads every artifact off disk per stage), and its
   `Path.read_text()` read-back has no explicit encoding. Both touch `src/`, so fixing them would
   need a fresh-session `architect-review`; decide if they block the merge or ride along after.
4. **The BL-12/BL-14 pattern** — worth an explicit check in the merge plan for any other file that
   needs to live on the default branch to actually function.

Small housekeeping alongside: once PR #54 merges, sprint 34 can be archived via `/archive-sprint`.

## Human actions
- `allow_rebase_merge: false` — **already set** (confirmed this session).
- `allow_merge_commit` — **stays enabled** until the migration-merge plan executes it (BL-13);
  do not disable it before then.
- `sha_pinning_required: true` — should already be set (Task 1 merged well before this handoff).
- **Review PRs #50–53** (Dependabot, major-version action bumps) — real review, not a rubber-stamp.
- **Carried:** delete `glunk-works/loop-engine-v3-scratch` (private, issues #1–#6); trim the PAT's
  repo list.

## Pointers
- [`docs/backlog.md`](../docs/backlog.md) — BL-11 fully resolved. BL-12/BL-14 resolved (backport
  shape). BL-13 open by design (held human settings action).
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — every phase closed since sprint 32
  (2026-07-12). Its own NEXT ACTION line still reads "none pre-selected" — the new planning task
  above is what fills that in.
- [`sprints/34_ci_supply_chain_hardening/sprint_plan.md`](../sprints/34_ci_supply_chain_hardening/sprint_plan.md)
  — closed. Its Task 4 "PAUSED" note and BL-13 "CORRECTED" note are historical record, not open items.
- `.ai/context/workflow.md` — the merge-commit exception for the migration landing is documented
  here; read it before scoping the new planning task.

## Working tree
- No active sprint branch. `sprint/34-ci-supply-chain-hardening` and `sprint/34-ruleset-drift` are
  dead (squash-merged) — **never push to a squash-merged branch again.**
  `sprint/34-bl14-dependabot-gap` has PR #54 open (green, docs-only), awaiting merge.
- `.ai/state.json` + `.ai/archive/` are git-ignored (local mirrors); **`.ai/next-steps.md` is
  tracked.**
