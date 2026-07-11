# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 6 — sprint `31_ralph_completion_integrity` — `planned`.**
Sprint 27 (the flip block) stays `planned_host_gated` behind it: V2 cannot pass
until sprint 31's fix lands. Sprint 31 is **planned, not yet implemented** —
next up is Sonnet implementing Task 1 + Task 2.

## Just done (Opus/Architect, 2026-07-11, host session)
- **Ran V2 re-attempt #7** on this session's daemon-bearing host (docker live,
  `loop-engine-dev:latest` present, keyring-backed Anthropic key present).
  Confirmed sprint 30's F-RALPH-OVERSPEC-TEST fix holds (did not recur), but
  found a new, more serious, **deterministic** defect: **F-RALPH-FALSE-COMPLETION**
  — `RalphCoderPersona` marks a manifest task "completed" based only on whether
  the model raised an open question, never checking whether `apply_file_blocks`
  actually applied its edit. Combined with the per-task report never being
  revisited once "done," one malformed/unattempted edit block on an
  already-"completed" task permanently wedges the sprint's report, blocking the
  pytest gate forever until the revise cap exhausts and escalates. Full
  root-cause writeup + evidence in `sprints/DEFERRED_VERIFICATION.md` (new
  section after F-RALPH-OVERSPEC-TEST) and `scratch/v2_rerun7.log` /
  `v2_escalations_rerun7.jsonl` / `v2_rerun7_state_snapshot.json`.
- **Planned the fix: sprint `31_ralph_completion_integrity`**
  (`sprints/31_ralph_completion_integrity/sprint_plan.md`). Scope: fix lives
  entirely in `personas/coder_iac/ralph.py`'s completion bookkeeping (FD1 — no
  `core/coder_gate.py` change needed; the gate machinery is sound once
  completion is honest). Task 1: change `_finalize_report` to return
  `(report, failures)` and gate `completed_tasks` on `failures` being empty
  (not just on no open question), with new tests. Task 2: reconcile
  `DEFERRED_VERIFICATION.md` once Task 1 lands. Classic `CoderIacPersona` is
  explicitly out of scope (FD2 — doesn't share the bug, slated for deletion in
  sprint 27 Task 4 anyway).

## Next
1. **Sonnet implements sprint 31** (`sprints/31_ralph_completion_integrity/sprint_plan.md`,
   Task 1 then Task 2). Run the green gate (full suite + lint/format/audit).
2. **Opus HITL review** of the diff — confirm it's scoped to exactly
   `personas/coder_iac/ralph.py` + `tests/personas/test_ralph_coder.py` (Task 1)
   and `sprints/DEFERRED_VERIFICATION.md` (Task 2), per FD1/FD2 — no
   `core/coder_gate.py`, no classic-persona, no engine/`State` changes.
3. **On HITL approval:** re-attempt V2 (#8) on a daemon-bearing host — reuse
   the same staging recipe (`scratch/v2_run_harness.py`,
   `scratch/v2_requirements_min.md`, fresh throwaway tree, full production
   config, injected `issue_filer`). Do NOT mark V2 PASS until a real container
   run reaches terminal `COMPLETED`. A re-wedge on an edit-application failure
   means sprint 31's fix was insufficient — re-open FD1, don't just re-tweak.
4. **On V2 PASS:** the subtractive sprint 27 flag deletions unblock (remove
   `ENGINE`/`TOOLS`/`PERSONAS` classic paths + `artifacts` strip + `loop.py`
   collapse + the issue-path default-flip carrying Sprint 26 findings R1–R7;
   Task 4 `CODER=ralph` gated on V2).

## HITL gate
Sprint 31 is planned but **not yet implemented** — no diff exists yet to
review. Once Sonnet implements Tasks 1–2, this becomes an open Opus HITL
review gate before another V2 host attempt (see step 2 above).

## Pointers
- `sprints/31_ralph_completion_integrity/sprint_plan.md` — the F-RALPH-FALSE-COMPLETION fix (planned this session; not yet implemented).
- `sprints/27_phase6_flip_block/sprint_plan.md` — the flip block (planned, host-gated); its V2 is the held-open `COMPLETED` obligation, now additionally gated on sprint 31.
- `sprints/30_ralph_test_scope/sprint_plan.md` — the prompt-only F-RALPH-OVERSPEC-TEST fix (complete, archived; verified holding by V2 re-attempt #7).
- `sprints/DEFERRED_VERIFICATION.md` — V1 PASS(qualified); **V2 OPEN**, gated on **F-RALPH-FALSE-COMPLETION** (fix planned: sprint 31); V3 not started.
- `docs/migration_roadmap.md` — Phase 6 row + NEXT ACTION (needs updating for sprint 31 — not yet done).
- `docs/backlog.md` — BL-1..BL-5.

## Working tree
- HEAD `6e1203e`. This session's delta — `sprints/DEFERRED_VERIFICATION.md`
  (new F-RALPH-FALSE-COMPLETION finding + status updates), the new
  `sprints/31_ralph_completion_integrity/sprint_plan.md`, and this
  `.ai/next-steps.md` reseed — is **uncommitted**; commit it to make the
  finding + plan durable before switching model/session. `docs/migration_roadmap.md`
  has NOT yet been updated for sprint 31 (do that alongside, or fold into
  sprint 31's Task 2). Untracked `scratch/` (V2 specs/run logs/harness/evidence)
  remains out of all commits — not for commit. `.ai/state.json` is git-ignored
  (local mirror only) and already reflects sprint 31 / assigned_model=sonnet.
