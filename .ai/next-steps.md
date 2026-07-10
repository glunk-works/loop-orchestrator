# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 5 — Sprint 25 (`bootstrap_flow`, piece 4) — `planning`.**
No sprint_plan yet. The next session is an **Opus/Architect** planning pass
(one question at a time, HITL gates) to write `sprints/25_bootstrap_flow/sprint_plan.md`.

## Just done (Sprint 24 — `maintenance_flow` — archived)
- Sprint 24 (maintenance flow, capability slice) is **implemented, HITL-reviewed,
  review-fixed, and archived** (`6172ad1` → `f8d388a`). Landed `tools/git_io`
  (the 4th sanctioned subprocess surface), `runner.run_in_tree`, and the
  `flows/maintenance` package (clone → branch → run → completion guard →
  no-change guard → green gate → green-only push/PR).
- HITL review (Opus) found + fixed 2 findings (`f8d388a`): the flow now requires
  the inner run to end `COMPLETED` before the gate (else `run_incomplete`, so a
  human-paused `AWAITING_ISSUE` tree is never shipped as a PR) and probes
  `git_io.has_changes` before committing (else `no_changes`, dodging
  `commit_all`'s empty-index crash). 497 tests green, lint/format/audit clean,
  `sbom.json` unchanged.

## Next
1. **(Opus/Architect) Plan Sprint 25 (bootstrap flow, piece 4).** Per the
   roadmap's "Deferred" note: `create_repository` in `glunk-works` → scaffold
   (`hatch new` / OpenTofu) in a fresh worktree → inject the global `CLAUDE.md`
   → commit/push. Separately planned + gated; deliver as
   `sprints/25_bootstrap_flow/sprint_plan.md`.
2. Handoff to Sonnet to implement once the plan is HITL-approved.

## Carry-forward
- **Low test-coverage nit (from the Sprint 24 review, not yet addressed):**
  `flows/maintenance.flow._default_run_tests` (the real green-gate glue —
  chdir into the clone + `run_pytest("src")`) is never exercised; every flow
  test injects a fake `run_tests`. A small unit test over `_default_run_tests`
  against a tmp clone with a trivial passing/failing `src/` test would close it.
  Orthogonal to Sprint 25 — pick up opportunistically or fold into the deferred
  live verification.
- **Open low nit (carried from 22b, still unresolved):** bare `python` vs
  `sys.executable` in the committed `loop_engine.mcp.json` github stanza —
  orthogonal to the flows work, not touched in 24.

## Pointers
- `docs/migration_roadmap.md` — Phase 5 status; ▶ NEXT ACTION → plan Sprint 25.
- `.ai/context/workflow.md` — the Opus↔Sonnet handoff protocol + switch points.
- `sprints/24_maintenance_flow/sprint_plan.md` — the just-archived sprint (the
  precedent capability-slice shape Sprint 25 mirrors).

## Working tree
- Sprint 24 committed at `f8d388a`. The archival edits (this `next-steps.md`,
  `.ai/state.json`, `docs/migration_roadmap.md`) are **uncommitted** — commit
  them to make the cursor advance durable.
