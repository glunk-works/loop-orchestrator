# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 6 — sprint `30_ralph_test_scope` — implemented, pushed, awaiting Opus HITL
review (→ Opus/Architect).** The prompt-only F-RALPH-OVERSPEC-TEST fix (locked
**FD1/FD2** — no gate-guard, additive directives only) is code-complete.

## Just done (Sonnet/Coder session, 2026-07-11)
- **T1** (`551338a`) — added the test-scope guardrail to `PROMPT_TEMPLATE`
  (`coder_iac/shared.py`: tests must cover only the enumerated acceptance criteria,
  no private/underscore-internal or import-mechanics assertions) and the
  self-fix-before-escalate guardrail to Ralph's per-increment prompts
  (`_build_task_prompt`/`_build_repair_prompt`, `ralph.py`: fix/remove a
  self-authored failing test in-scope; `## Open Questions` reserved for genuine
  spec ambiguities only). Unit tests pin both new directives and confirm the
  existing ones (implement-only-this-task, Global-DoD, no-secrets,
  escalate-genuine-ambiguity) survive.
- **T2** (`f934fda`) — reconciled `sprints/DEFERRED_VERIFICATION.md`:
  F-RALPH-OVERSPEC-TEST now reads resolved-in-code (sprint 30, `551338a`); V2's
  section notes its last in-code blocker is closed, host `COMPLETED` is the sole
  remaining obligation.
- Full suite (580 tests), lint, format, audit all green; `sbom.json` unchanged (no
  dependency changes). Both commits pushed to `feat/mcp-langgraph-migration`.

## Next
1. **Opus HITL-reviews** `551338a` + `f934fda` against the sprint plan's locked
   decisions (FD1: prompt-only, no gate-guard; FD2: additive, not a scope
   renegotiation) and the acceptance criteria. If approved, sprint 30 is done —
   run `/archive-sprint`.
2. **Then a fresh V2 re-attempt** (host, Opus, real budget) — reuse the run-#6
   staging recipe (harness `scratch/v2_run_harness.py`, tree `scratchpad/v2_tree`,
   `LOOP_ENGINE_DEV_IMAGE=loop-engine-dev:latest`, injected `issue_filer`, absolute
   env python). Only this host `COMPLETED` *verifies* F-RALPH-OVERSPEC-TEST +
   discharges V2. A re-run that still escalates on a self-authored test ⇒
   prompt-only was insufficient ⇒ escalate to the deferred gate-guard (FD1
   fallback), don't just re-tweak wording.
3. **On V2 PASS:** sprint-27 flag deletions unblock (Task 4 `CODER=ralph` gated on V2).

## HITL gate
**OPEN** — Opus review owed on sprint 30 commits `551338a` (T1) and `f934fda` (T2)
before the sprint is archived. Separately, host-gated: V2 `COMPLETED` (now gated only
on the host re-run) and V3 (not started). No sprint-27 deletion lands until V2 + V3 pass.

## Pointers
- `sprints/30_ralph_test_scope/sprint_plan.md` — the prompt-only fix (implemented,
  awaiting review).
- `sprints/DEFERRED_VERIFICATION.md` — V1 PASS(qualified); V2 OPEN (host re-attempt
  only); F-RALPH-OVERSPEC-TEST resolved-in-code (sprint 30); V3 not started.
- `sprints/27_phase6_flip_block/sprint_plan.md` — the flip block (host-gated).
- `docs/migration_roadmap.md` — Phase 6 row + NEXT ACTION.

## Working tree
- HEAD `f934fda` (pushed). Clean except untracked `scratch/` (V2 specs/logs/harness/
  pubkey) — out of all commits. `.ai/state.json` is git-ignored (local mirror only).
