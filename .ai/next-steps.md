# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 6 — sprint `27_phase6_flip_block`: Task 10 (the F1–F7 review fixes) has landed**
on PR #34, head commit `654d14a`. It has **not yet been re-reviewed** — the prior
CHANGES REQUESTED review was against the old head (`be50d61`) and is invalidated by the
push. Task 9 (delete `DEFERRED_VERIFICATION.md`, close Phase 6) stays **blocked** until
this review passes.

## Just done (Sonnet/Coder, 2026-07-12)
Implemented all seven Task 10 findings on `sprint/27-task8-followup`, commit `654d14a`:
- **F1/F2 — resume guard.** `cli.py`'s `resume --snapshot` now derives repo *and* issue
  number from the snapshot's own `pending_issue.url` via a new
  `issue_io.repo_from_issue_url` (never CWD). `resume --from-issue` alone resolves its
  repo explicitly and **echoes it** before doing any work — the echo is the actual
  defense; no downstream comparison can detect a human resuming from the wrong
  checkout. Rewrote `test_cli_resume_rejects_a_same_numbered_issue_from_the_wrong_repo`
  to construct the *real* scenario (a genuine, unrelated same-numbered issue) and assert
  what actually happens — it resumes, silently, with only the echo as the tell.
- **F3/F6 — concurrency.** `tools/state_io/writer.py`'s `_STATE_ROOT` and
  `tools/worktree/manager.py`'s `_ORIGIN_CWD` are now `contextvars.ContextVar`s, set/
  reset by token (closes F6's non-re-entrancy in the same change — nesting no longer
  clobbers to `None`). `trigger/dispatch.py`'s `InProcessDispatcher` gained a lock
  serializing actual loop execution, since `os.chdir` itself stays process-global
  regardless. Filed **BL-8** (`docs/backlog.md`) for the real fix.
- **F4 — crash-losing pause path.** `core/engine.py::_pause_for_issue` now persists the
  `AWAITING_ISSUE` snapshot *before* filing. A new `RepoNotResolvableError`
  (`tools/repo_io/github.py`) lets `tools/issue_io/mcp_client.py` raise a typed
  `IssueDestinationUnresolvedError` on an unresolvable destination **without** itself
  importing `subprocess` (kept `resolve_repo_slug`'s failure mode from leaking a raw
  `CalledProcessError` across the module boundary — and incidentally kept
  `test_subprocess_surfaces.py` green). No `repo=None` fallback anywhere.
- **F5 — soft-fail guard.** A missing `url` on a read issue now raises instead of
  skipping the integrity check.
- **F7 — import-time coupling.** `mcp_client.py`'s `tools/mcp`/`tools/repo_io`/
  `tools/worktree` imports moved into `default_issue_filer`/`default_issue_reader`
  (function-scoped). `CLAUDE.md`'s `core/` boundary bullet reverted to its pre-#34
  wording: `core/engine` no longer pulls the MCP client stack in at import time.

Suite green (538 passed), `lint`/`format`/`audit` clean, `sbom.json` unchanged (no dep
changes). Pushed to `sprint/27-task8-followup`.

## Next
1. **A fresh Opus session reviews PR #34 at head `654d14a`** and posts via
   `gh pr review 34 --comment` with the required header + fresh-session attestation
   (`.github/workflows/hitl-review.yml`). Cross-check each F1–F7 fix against the prior
   review's reasoning/failure traces (`gh pr view 34 --comments`), not just the sprint
   plan's fix designs.
2. **If approved:** Task 9 (delete `sprints/DEFERRED_VERIFICATION.md`, mark Phase 6 done
   in the roadmap) on the same branch, then the deferred `State.artifacts` strip as its
   own sprint (FD3), then `/archive-sprint`.
3. **If changes are requested:** spec the new findings as a follow-up task the same way
   Task 10 was specced, and hand back to Sonnet/Coder.

**Model: Opus/Architect** for the review; Sonnet/Coder only returns if it comes back
with changes requested.

## HITL gate
**PR #34, head `654d14a`: awaiting a fresh-session review.** Must not merge until that
review passes (or its findings are fixed and re-reviewed). The owner's merge is the
approval; Claude never merges or force-pushes.

## Pointers
- `sprints/27_phase6_flip_block/sprint_plan.md` — Task 10 (F1–F7) now DONE. Tasks
  0–4/6/7/8/10 done, 5 deferred (FD3), 9 blocked on this review.
- PR **#34**'s prior review comment — the F1–F7 reasoning and failure traces
  (`gh pr view 34 --comments`); the new review should verify the fixes against it.
- `docs/backlog.md` — **BL-8**, filed by Task 10.
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
- Work continues on **`sprint/27-task8-followup`** (at `654d14a`), which *is* PR #34.
  Sprint branches squash-merge, so only the tip tree ships.
- `.ai/state.json` is git-ignored (local mirror); **`.ai/next-steps.md` is tracked** and
  lands via a PR like the previous cursor resyncs (#27, #29, #31).
