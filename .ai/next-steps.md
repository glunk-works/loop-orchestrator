# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 6 — sprint `31_ralph_completion_integrity` is `done` (HITL-approved).**
The active sprint is once again `27_phase6_flip_block`, still host-gated: V2 has
never observed a terminal `COMPLETED`, and re-attempt **#8** is the obligation.

## Just done (Opus/Architect, 2026-07-11)
- **Sprint 31 HITL review — PASSED.** Scope confirmed exactly `personas/coder_iac/ralph.py`
  + `tests/personas/test_ralph_coder.py` (`e5d9d98`) and `sprints/DEFERRED_VERIFICATION.md`
  (`9c32cbf`) — no `core/coder_gate.py` (FD1), no classic persona (FD2), no engine/`State`
  change; the edit-failure state is kept distinct from an escalation (FD3). Verified
  empirically that `_upsert_task_section`'s regex really does clear the stale
  `## Edit Application Failures` marker on a successful retry — the property FD1's
  "no gate change needed" argument rests on.
- **`b23f1b7` (review follow-ups):** a test assertion pinning that marker-clearing at
  the seam that matters, + `docs/migration_roadmap.md` finally updated for sprint 31
  (Phase 6 row + NEXT ACTION now name re-attempt #8).
- **NEW WORKFLOW — PR-gated integration (`1b501a0`, PR #22, CI green, awaiting merge).**
  The owner raised the host pinentry timeout to 4h, so Claude now commits/pushes
  unattended (signing is non-interactive; confirmed). In exchange: sprint work lands on
  a `sprint/NN-slug` branch cut from `feat/mcp-langgraph-migration`, opens a PR **based on
  that branch, not `main`**, and **Claude never merges or force-pushes** — the owner's
  merge is the approval. Written into `CLAUDE.md` + `.ai/context/workflow.md`.
- **Gap this surfaced:** `.github/workflows/ci.yml` fires only on `pull_request:` and
  pushes to `main` — so **every sprint commit pushed straight to
  `feat/mcp-langgraph-migration` (sprints 26–31) has run zero CI.** The PR flow turns it
  on. Optional backstop, not yet done: add the integration branch to the push trigger.

## Next
1. **V2 re-attempt #8** (Opus/Architect — real budget). **First probe `docker info`.**
   No daemon ⇒ record the blocker and stop; do not burn budget. Daemon present ⇒ reuse
   the run-#7 staging recipe (`scratch/v2_run_harness.py`, `scratch/v2_requirements_min.md`,
   fresh throwaway tree, `LOOP_ENGINE_ISOLATION=container`, `LOOP_ENGINE_CODER=ralph`,
   full production config, injected `issue_filer`, absolute env python).
   Do **not** mark V2 PASS until a real container run reaches terminal `COMPLETED`.
   A re-wedge on an edit-application failure means sprint 31's fix was insufficient —
   re-open FD1 (reconsider the deferred `edit_findings` scan-scope narrowing), don't re-tweak.
2. **On V2 PASS:** the subtractive sprint 27 flag deletions unblock (remove
   `ENGINE`/`TOOLS`/`PERSONAS` classic paths + `artifacts` strip + `loop.py` collapse +
   the issue-path default-flip carrying Sprint 26 findings R1–R7; Task 4 `CODER=ralph`).
3. `/archive-sprint` for sprint 31 whenever convenient (it is done + approved + committed).

## HITL gate
**Sprint 31: CLOSED** (reviewed and approved 2026-07-11).
**Standing gate (new):** every sprint now lands via a PR into
`feat/mcp-langgraph-migration`; the owner's merge is the approval. **PR #22 is open,
CI green, awaiting the owner's merge** — it is the workflow change itself.

## Pointers
- `sprints/27_phase6_flip_block/sprint_plan.md` — the active sprint (host-gated on V2 #8).
- `sprints/31_ralph_completion_integrity/sprint_plan.md` — done/approved; its FD1 holds the re-wedge escalation rule.
- `sprints/DEFERRED_VERIFICATION.md` — V1 PASS(qualified); **V2 OPEN** (host `COMPLETED` never observed); F-RALPH-FALSE-COMPLETION + F-RALPH-OVERSPEC-TEST both resolved-in-code; V3 not started.
- `docs/migration_roadmap.md` — Phase 6 row + NEXT ACTION (current as of `b23f1b7`).
- `.ai/context/workflow.md` — the PR-gated integration protocol.
- `docs/backlog.md` — BL-1..BL-5.

## Working tree
- On branch `chore/pr-gated-workflow` @ `1b501a0` (PR #22). `feat/mcp-langgraph-migration`
  is at `b23f1b7`; the two differ by docs only, so either branch is fine to run V2 from.
  Untracked `scratch/` (V2 harness/logs/evidence) stays out of all commits.
  `.ai/state.json` is git-ignored (local mirror only).
