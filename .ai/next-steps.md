# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 6 — sprint `27_phase6_flip_block`: Task 8 landed (PR #32); its follow-up PR #34 is
OPEN with CHANGES REQUESTED.** Task 10 (the review fixes) is the live task. Task 9 — deleting
`DEFERRED_VERIFICATION.md` and closing Phase 6 — is **blocked on it**: the issue path is not
proven while it carries an open correctness defect.

## Just done (Opus/Architect, 2026-07-12)
- **Resolved PR #34's merge conflict** against the updated base (#35/#36 had landed). Only
  `tests/test_ci_config.py` conflicted — base and branch each appended a test at the same
  point; both kept. 528 green. *(The merge commit also swept in the untracked `scratch/` tree
  via `git add -A`; removed again in `fc3e9db`, and `scratch/` is now gitignored — `.gitignore`
  had only `.scratch/`. No credential material was involved.)*
- **Posted the fresh-session Opus/Architect HITL review of #34** — the first PR through the new
  `hitl-review.yml` gate. `architect-review` is green.
- **Verdict: changes requested.** #34's *altitude* is right — the escalation destination
  belongs inside `default_issue_filer`, not threaded from each entrypoint — but two of its
  three mechanisms don't hold, and it made a run-losing crash path reachable.
- **Specced the fixes as Task 10** (`1ad2dcd`), findings **F1–F7**, on the same branch.

### The three that matter
- **F1/F2 — the wrong-repo resume guard is a tautology.** It compares the issue read against a
  snapshot parsed *out of that same issue*, so both sides agree by construction. The real
  hazard (reading loop-engine's own #17 instead of `acme/managed#17`) sails straight through
  and **silently resumes the wrong run**. Its test passes only by stubbing an impossible
  pairing. **The reframe that drives the fix: there is no inconsistent state to detect** — the
  resumed run genuinely *is* paused on the issue genuinely read; it just isn't the one the
  human meant. Fix the *input* ambiguity; don't strengthen the comparison.
- **F3/F6 — `_ORIGIN_CWD` is a process-global and the trigger runs loops concurrently.**
  `InProcessDispatcher` dedupes only on `(repo, issue)`, so concurrent runs clobber each
  other's origin — **the R8 leak returns** in the one surface built for many runs.
  `ContextVar` + a dispatcher lock. (`os.chdir` stays process-global — that's **BL-8**.)
- **F4 — a failed escalation destroys the run.** `_pause_for_issue` files the issue *before*
  `_finalize` persists, so a raise in the filer loses everything. #34 made it reachable via an
  unconditional `gh repo view`. Persist first, file second.

## Next
1. **Task 10 — implement F1–F7** on the **existing** `sprint/27-task8-followup` branch (not a
   new one: #34 is open, this is review-fix flow). Order: **F4 → F1/F2 → F3/F6 → F5/F7**.
   Full spec + fix designs are in the sprint plan; the failure traces are in the PR #34 review
   comment (`gh pr view 34 --comments`).
2. **A fresh Opus session re-reviews** — pushing to the branch invalidates the current review,
   and the gate rejects a review from the session that wrote the diff.
3. Then **Task 9** (delete `DEFERRED_VERIFICATION.md`, close Phase 6), then the deferred
   `State.artifacts` strip as its own sprint (FD3), then `/archive-sprint`.

**Model: Sonnet/Coder** — the spec is fully determined. Opus returns only for the review.

## HITL gate
**PR #34: changes requested.** It must not merge until Task 10 lands and a **fresh** Opus
session re-reviews against the new head SHA. The owner's merge is the approval; Claude never
merges or force-pushes.

## Pointers
- `sprints/27_phase6_flip_block/sprint_plan.md` — **Task 10** is live (F1–F7 + fix designs).
  Tasks 0–4/6/7/8 done, 5 deferred (FD3), 9 blocked on 10.
- PR **#34**'s review comment — the reasoning and failure traces behind F1–F7.
- `docs/migration_roadmap.md` — decisions log (FD1/FD2/FD3), NEXT ACTION.
- `.ai/context/workflow.md` — PR-gated integration + the fresh-session review rule.
- `.github/workflows/hitl-review.yml` — the gate itself (#35/#36).

## Live external state — needs cleanup (HUMAN ACTION)
- **`glunk-works/loop-engine-v3-scratch`** (private) is still live, holding issues **#1–#6**.
  Delete it in the GitHub UI, then remove it from the fine-grained PAT's repo list (the PAT has
  no `Administration` permission by design, so it cannot delete repos — that stays a human
  checkpoint on the one irreversible action; it also carries an unexpected `Contents: Write`
  worth trimming while you're there).

## Working tree
- Work continues on **`sprint/27-task8-followup`** (at `1ad2dcd`), which *is* PR #34. Sprint
  branches squash-merge, so the merge commit + scratch-removal commit in its history vanish on
  merge; only the tip tree ships.
- `scratch/` is untracked **and now gitignored**. It stays out of all commits.
- `.ai/state.json` is git-ignored (local mirror); **`.ai/next-steps.md` is tracked** and lands
  via a PR like the previous cursor resyncs (#27, #29, #31).
