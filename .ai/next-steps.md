# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 6 — sprint `31_ralph_completion_integrity` — `awaiting_hitl_review`.**
Sprint 27 (the flip block) stays `planned_host_gated` behind it: V2 cannot pass
until this sprint's HITL review clears and a fresh host re-attempt (#8) observes
`COMPLETED`.

## Just done (Sonnet/Coder, 2026-07-11)
- **Task 1 (`e5d9d98`):** `_finalize_report` (`personas/coder_iac/ralph.py`) now
  returns `(report, failures)` instead of just `report`. `_task_increment`'s
  completion branch is broadened so a task is marked done only when there were
  no new questions **and** no edit-application failures; a failure-without-a-
  question case (FD3) leaves `blocked_items`/`state.questions` untouched, writes
  a distinct non-escalation memory outcome, and leaves the task selectable
  again next increment. `_repair`'s call site updated to unpack the new tuple.
  Three new tests added (`tests/personas/test_ralph_coder.py`); all prior Ralph
  tests pass unmodified.
- **Task 2 (`9c32cbf`):** `sprints/DEFERRED_VERIFICATION.md` — F-RALPH-FALSE-COMPLETION
  marked resolved-in-code against `e5d9d98`; V2 section gets a sprint-31 status
  update restating the remaining host V2 re-attempt #8 obligation.
- Full suite, lint, format all green (doc-only Task 2, no `sbom.json` change).

## Next
1. **Opus HITL review** of both commits — confirm scope is exactly
   `personas/coder_iac/ralph.py` + `tests/personas/test_ralph_coder.py` (Task 1)
   and `sprints/DEFERRED_VERIFICATION.md` (Task 2), per FD1/FD2/FD3 — no
   `core/coder_gate.py`, no classic-persona, no engine/`State` changes.
2. **On HITL approval:** re-attempt V2 (#8) on a daemon-bearing host — reuse the
   same staging recipe (`scratch/v2_run_harness.py`, `scratch/v2_requirements_min.md`,
   fresh throwaway tree, full production config, injected `issue_filer`). Do NOT
   mark V2 PASS until a real container run reaches terminal `COMPLETED`. A
   re-wedge on an edit-application failure means sprint 31's fix was
   insufficient — re-open FD1, don't just re-tweak.
3. **On V2 PASS:** the subtractive sprint 27 flag deletions unblock (remove
   `ENGINE`/`TOOLS`/`PERSONAS` classic paths + `artifacts` strip + `loop.py`
   collapse + the issue-path default-flip carrying Sprint 26 findings R1–R7;
   Task 4 `CODER=ralph` gated on V2).

## HITL gate
**OPEN.** Opus must review sprint 31's diff (`e5d9d98` + `9c32cbf`) before
sprint 27's V2 re-attempt #8. No V2 re-attempt until this review passes.

## Pointers
- `sprints/31_ralph_completion_integrity/sprint_plan.md` — the F-RALPH-FALSE-COMPLETION fix (implemented; awaiting HITL review).
- `sprints/27_phase6_flip_block/sprint_plan.md` — the flip block (planned, host-gated); its V2 is the held-open `COMPLETED` obligation, now additionally gated on sprint 31's HITL review + host re-attempt.
- `sprints/30_ralph_test_scope/sprint_plan.md` — the prompt-only F-RALPH-OVERSPEC-TEST fix (complete, archived; verified holding by V2 re-attempt #7).
- `sprints/DEFERRED_VERIFICATION.md` — V1 PASS(qualified); **V2 OPEN** (host `COMPLETED` not yet observed); F-RALPH-FALSE-COMPLETION resolved-in-code (sprint 31); V3 not started.
- `docs/migration_roadmap.md` — Phase 6 row + NEXT ACTION (still needs updating for sprint 31 — not yet done).
- `docs/backlog.md` — BL-1..BL-5.

## Working tree
- HEAD `9c32cbf`. Tasks 1 and 2 are both committed. Untracked `scratch/`
  (V2 specs/run logs/harness/evidence) remains out of all commits — not for
  commit. `.ai/state.json` is git-ignored (local mirror only) and already
  reflects sprint 31 / `awaiting_hitl_review` / assigned_model=opus.
  `docs/migration_roadmap.md` has NOT yet been updated for sprint 31.
