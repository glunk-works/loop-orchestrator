# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`, `docs/backlog.md`) + the active sprint file — it does not
copy them. Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**The migration is fully closed** (Phases 1–6). Nothing here is migration work.

**Current unit: sprint `33_ci_title_starvation` (BL-10) — status `awaiting_hitl_review`.**
Tasks 1–4 are implemented, committed, and pushed. **PR #43 is open** (base
`feat/mcp-langgraph-migration`). **Opus/Architect** picks up next — Task 5 (live GitHub
verification) plus a fresh-session HITL review are both Opus/human work.

## Just done (Sonnet/Coder implementation session, 2026-07-12)
- **Task 1** (`3210867`) — new `.github/workflows/pr-title.yml`, `pr-title` job moved
  verbatim, job id frozen exactly as `pr-title` (FD5).
- **Task 2** (`9dd6922`) — cut `pr-title` out of `ci.yml`: dropped `edited` from the
  trigger types, deleted `needs: pr-title` and `lint`'s `if:` block, rewrote the stale
  comments. **Suite went red on purpose here** (FD3) — expected, not a bug.
- **Task 3** (`8e33f38`) — deleted `test_lint_job_gates_on_pr_title_to_fail_fast` (it
  pinned the bug); added five structural `yaml.safe_load` tests for the real invariant
  (no `if:` anywhere in `ci.yml`, no `needs:` mentions `pr-title`, `edited` excluded from
  `ci.yml`'s triggers, `pr-title.yml`'s job id/triggers/no-`needs:` shape). Suite green
  again: **541 passed.**
- **Task 4** (`89ac2e8`) — rewrote `CLAUDE.md` L86 (no longer claims the heavy chain gates
  on `pr-title`); marked **BL-10 resolved by sprint 33** in `docs/backlog.md`, recording
  both FD2 (the `concurrency`-cancellation path BL-10's own preferred fix would not have
  closed) and FD3 (the green test that pinned the defect).
- **Pushed and opened [PR #43](https://github.com/glunk-works/loop-engine/pull/43).**

## ⚠ Immediate blocker before Task 5
**PR #43 is `mergeStateStatus: DIRTY` / `mergeable: CONFLICTING` — CI has not run on it
at all yet** (`statusCheckRollup` is empty). Cause: the base branch picked up commit
`476ce8d` (PR #42, a squash-merge of the old `docs/handoff-sprint-33` branch) which is
byte-identical in *content* to `da1c6eb` — the commit this sprint branch still carries —
but has a different SHA, so git sees it as a real divergence. `git merge-tree --write-tree
HEAD origin/feat/mcp-langgraph-migration` shows exactly **one** conflicting file:
`.ai/next-steps.md` (both branches independently evolved this cursor since the common
ancestor `6a9c77a`).

**Fix:** merge `origin/feat/mcp-langgraph-migration` into `sprint/33-ci-title-starvation`
(a merge commit — **not a rebase**, since the branch is already pushed and rebasing would
need a force-push). Resolve `.ai/next-steps.md` by keeping *this* file's content (it's the
newer, more complete cursor). Push normally (not `--force`). Re-check with
`gh pr view 43 --json mergeStateStatus,mergeable,statusCheckRollup` before starting Task 5
— CI needs a clean merge state to run at all.

## Next — Opus/Architect: Task 5 + HITL review
Once PR #43 is clean and CI has actually run:

1. Edit the PR title to something **deliberately >72 chars** (still a valid Conventional
   Commits subject otherwise). **Expect:** `pr-title` goes red; `lint`/`test`/
   `secrets-scan`/`dependency-audit` **all run anyway and go green** on the same commit —
   under the old config every one of them would have reported `skipped`. That single
   observation closes **BL-10**.
2. Fix the title back to something valid. **Expect:** `pr-title` flips green via `edited`;
   **no new `ci.yml` run fires at all**, and the heavy chain's existing conclusions stay
   `success` — not `skipped`, not `cancelled`. That closes **FD2**.
3. Post both observations on the PR so the record survives the merge.
4. **Human-only:** confirm in the GitHub UI that the required check `pr-title` still
   resolves against the new `pr-title.yml` workflow (FD5) — Claude is 403 on branch
   protection, cannot check this itself.
5. Post a fresh-session Opus HITL review (`gh pr review 43 --comment`, **never
   `--approve`**) even though `hitl-review.yml`'s `^src/` filter exempts this PR — the
   diff's whole subject *is* the gate machinery. Sharpest questions: is the job id still
   exactly `pr-title` (FD5)? Would any test still pass if `edited` were re-added to
   `ci.yml` (FD4)?

## Standing obligations (not sprint-33 tasks; all still real)
- **`sprints/DEFERRED_VERIFICATION.md`** — five checks (§1, §5, §6, §7, §8) **never run**. Don't delete it.
- **Two unfixed findings from PR #39** — `publish_artifacts` reads every artifact off disk on every
  stage while both docstrings claim it *"does no I/O"*; that read-back uses `Path.read_text()` with
  no explicit encoding. **Deliberately out of sprint 33's scope** (they touch `src/`).
- **Human:** after PR #43 merges, delete `docs/handoff-sprint-33` (now redundant twice
  over — its content is on the base branch as `476ce8d` too); `glunk-works/loop-engine-v3-scratch`
  (private, issues #1–#6) is still live and needs deleting in the UI, then trimming from
  the PAT's repo list. Neither done yet.

## Pointers
- [`sprints/33_ci_title_starvation/sprint_plan.md`](../sprints/33_ci_title_starvation/sprint_plan.md) — **the sprint.** FD1–FD5 + Tasks 1–5; Task 5's Description/Acceptance Criteria is the next read.
- [`docs/backlog.md`](../docs/backlog.md) — **BL-10 now marked resolved**, FD2/FD3 recorded.
- [PR #43](https://github.com/glunk-works/loop-engine/pull/43) — head `sprint/33-ci-title-starvation`, base `feat/mcp-langgraph-migration`.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — every phase closed, untouched by sprint 33.
- `.ai/context/workflow.md` — PR-gated integration + the fresh-session review rule.

## Working tree
- `sprint/33-ci-title-starvation` (at `89ac2e8`, pushed) is the active branch. PR base is
  **`feat/mcp-langgraph-migration`**. Currently conflicts with base — see blocker above;
  resolve with a merge commit, not a rebase. Branches squash-merge — **a squash-merged
  branch is dead; never reuse one.**
- `.ai/state.json` + `.ai/archive/` are git-ignored (local mirrors); **`.ai/next-steps.md` is tracked.**
