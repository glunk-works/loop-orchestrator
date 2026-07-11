# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 6 — sprint `27_phase6_flip_block` is active and its host gate is DISCHARGED.**
**V2 is PASS.** The subtractive flag deletions (Tasks 1–4) are the next real work, and
they are the last thing standing between here and the end of the migration's flag era.

## Just done (Opus/Architect, 2026-07-11)
- **V2 re-attempt #8 — PASS.** A real container-sandboxed Ralph run reached terminal
  **`COMPLETED`** under the full production config (`langgraph` + `mcp` + `declarative`
  + `ralph` + `container`) — the observation V2 has been gated on since sprint 27.
  `run_id=0c8fdb89949c49578f891fe78f3373b4`; **8/8** manifest tasks across 3 sprints;
  **zero escalations**; **$2.2433 of $5.00** (vs run #3's `BUDGET_EXCEEDED`).
- **Independently re-verified** rather than trusting the gate's self-report: `pytest -q`
  in the produced worktree → 15 passed; `ruff check` + `ruff format --check` clean;
  `slugify`/`word_count` exercised directly against every spec case + both `TypeError`
  paths → all pass.
- **Sprint 31's fix held.** The run-#7 edit-application wedge did **not** recur, so
  **FD1 does not fire** and stays closed (its trigger was a *re-wedge on edit
  application*); the deferred `edit_findings` scan-scope narrowing stays deferred.
- **One invalid attempt (#8a), recorded on purpose** in `DEFERRED_VERIFICATION.md` so it
  is not later mined as a finding: it escalated on a target tree that was **mis-seeded**
  (`testpaths = ["tests"]`, no `pythonpath`, contradicting the spec's stated pre-seeded
  `pyproject.toml`). Staging error, not a product defect. **Lesson: seed the target tree
  exactly as the spec's `functional_requirements` describe the pre-seeded packaging.**
- **Merged: PR #26** (`9a70af4`) — CI `pull_request` trigger now includes `edited`, so a
  corrected PR title actually re-validates; a single `if: github.event.action != 'edited'`
  guard on `lint` skips the whole heavy chain on prose edits (verified live).
- **Merged: PR #25** (`2ea85df`) — the V2 PASS evidence (`DEFERRED_VERIFICATION.md` V2 →
  PASS, roadmap Phase 6 row + NEXT ACTION).
- **Repo setting fixed by the owner:** `squash_merge_commit_message` `BLANK` →
  `COMMIT_MESSAGES`. The `Sprint:`/`Finding:` trailers now **survive the squash** —
  `2ea85df` is the first integration-branch commit to actually carry `Sprint: 27`.
  (Everything before it, incl. `b751bd0`, has a permanently blank body. Not worth
  rewriting history over; the rationale lives in the sprint plans + this ledger.)

## Next
1. **Sprint 27's subtractive flag deletions (Tasks 1–4)** — now unblocked. Remove the
   `ENGINE`/`TOOLS`/`PERSONAS` classic paths, the `artifacts` strip, the `loop.py`
   collapse, and the issue-path default-flip (carrying Sprint 26 findings R1–R7);
   Task 4 makes `CODER=ralph` the default. This is a **large subtractive change across
   `core/`** — do an Opus/Architect planning pass first, then hand the mechanical
   deletions to Sonnet. Fresh `sprint/27-*` branch → PR into `feat/mcp-langgraph-migration`.
2. **V3** (the real `gh` round-trip: `repo_io`/`issue_io` against a live remote) is
   still not started — the last unstarted host verification.
3. `/archive-sprint` for sprint 31 whenever convenient (done + approved + committed).

## HITL gate
**No open gate. No open PRs.** Standing gate: every sprint lands via a PR into
`feat/mcp-langgraph-migration`; the owner's merge is the approval; Claude never merges
or force-pushes.

## CI gotcha worth keeping (learned the hard way, 2026-07-11)
For a `pull_request` event, GitHub reads `on.pull_request.types` from the **head
branch's** copy of `ci.yml` — *not* from the base, and *not* from the merge commit.
So merging a workflow-trigger fix into the base does **not** retroactively give an
already-open PR the new trigger: an edit to that PR fires **no run at all**. The fix
only reaches an open PR by bringing the base into its head (`git merge origin/<base>`
→ push, i.e. a `synchronize` event). Corollary: a stale `pr-title` failure on a PR cut
before `9a70af4` still cannot self-clear — merge the base in.

## Pointers
- `sprints/27_phase6_flip_block/sprint_plan.md` — the active sprint (host gate discharged).
- `sprints/DEFERRED_VERIFICATION.md` — V1 PASS(qualified); **V2 PASS** (#8); V3 not started.
- `docs/migration_roadmap.md` — Phase 6 row + NEXT ACTION (current as of `2ea85df`).
- `.ai/context/workflow.md` — the PR-gated integration protocol.
- `docs/backlog.md` — BL-1..BL-5.

## Working tree
- `feat/mcp-langgraph-migration` is at `2ea85df`. All sprint/chore branches through
  #26 are merged and deleted; **PRs squash-merge, so a merged branch is dead** — always
  cut new work from updated `origin/feat/mcp-langgraph-migration`.
- Untracked `scratch/` holds the V2 harness + run-#8 evidence (`v2_rerun8b.log`,
  `v2_run_harness.py`, `v2_requirements_min.md`); it stays out of all commits.
- `.ai/state.json` is git-ignored (local mirror only); `.ai/next-steps.md` **is tracked**
  and must land via a PR like any other file.
