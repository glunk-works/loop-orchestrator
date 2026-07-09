# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 4 · part 2 (sprint `21_declarative_review_fixes`) — `done`.** Sprint 21 is
implemented, HITL-reviewed, and its review findings are resolved + committed. The
HITL gate is **closed**. Nothing is in flight; the next action is archiving.

## Just done
- **(Opus / Architect) HITL-reviewed the sprint-21 implementation (`aceb23a`)** — high-effort `/code-review` scoped to that commit. Three findings surfaced and were all resolved this session in `03818d9`:
  1. **Finding #1 — false "inert for classic" guarantee.** The PM stage's `max_revisions=4` + `escalate_on_exhaustion=True` are live on the *classic* path too (its `ArtifactGate` returns REVISE on a missing/empty/invalid `project_spec`), so a non-converging classic PM now escalates to a human issue instead of hard-failing. **Owner chose to make it intentional (option 1):** corrected the `loop.py` + `test_default.py` comments and added `test_classic_default_loop_pm_stage_escalates_on_exhaustion` pinning the real classic PM stage.
  2. **Finding #2 — duplicated ESCALATE synthesis.** Extracted the identical no-progress / budget-exhausted escalation block into `core/engine.py::_exhaustion_escalation()`.
  3. **Finding #4 — key_merge findings accumulation.** **Settled: accepted as in-bounds non-parity (docs-only, no code change).** Accumulation is the engine's uniform revise-loop contract; a latest-only carve-out would be worse than the redundancy. Recorded in the roadmap decisions log + sprint-plan note + a comment at `_revise_key_merge`.
- **Committed:** `03818d9` — "Phase 4 part 2: sprint 21 HITL-review resolution" (7 files).
- **Green gate passing:** `hatch run test` (394 passed), `lint` (clean), `format` (clean).

## Next
1. **(Opus / Architect) `/archive-sprint`** — sprint 21 is complete, HITL-approved, and committed. Archive **20 and 21** (each is a separate archive step).
2. **(Opus / Architect) Begin Phase 5 planning** — FastAPI webhook triggers + the multi-repo factory (currently a sketch in the roadmap). Planning pass, one question at a time, HITL-gated.

## Pointers
- `docs/migration_roadmap.md` — deep status + decisions log (resume point of record); see the new "Sprint-21 HITL-review settlements" bullet.
- `sprints/21_declarative_review_fixes/sprint_plan.md` — the just-completed sprint (finding #4 note now marked RESOLVED).
- `sprints/20_declarative_generators/sprint_plan.md` — the reviewed/approved sprint the fixes derive from (also pending archive).
- `.ai/context/workflow.md` — the Opus↔Sonnet handoff protocol + switch points.
