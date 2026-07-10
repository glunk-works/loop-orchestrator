# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 6 — Collapse the flags (decommission the migration scaffolding) — `planning`.**
Phase 5 is done (22a/22b/23/23a/24/25 all complete, reviewed, archived). The next
session is an **Opus/Architect** planning pass that turns the roadmap's "Phase 6"
sketch into an actual sprint sequence. **No `sprint_plan.md` exists yet** — the
first planning pass writes it.

## Just done (Sprint 25 — `bootstrap_flow`, piece 4)
- Implemented + HITL-reviewed (Opus, approved) + **archived**. Impl at `79b535d`.
  Landed `tools/scaffold` (the **second** sanctioned file-write surface) + bundled
  Python templates + byte-identical conventions sync-guard, and `flows/bootstrap`
  (create → clone → checkout main → scaffold → commit → push main → create develop;
  skeleton-only, no inner loop/gate/PR). 525 tests green; lint/format/audit clean;
  `sbom.json` unchanged; subprocess surfaces unchanged (four).
- Review verdict: **APPROVE**. One non-blocking test-quality nit carried forward
  (two vacuous "no open_pr" assertions in the bootstrap tests — real protection is
  intact via the fakes lacking `open_pr`; cosmetic only).
- Cursor snapshot preserved at `.ai/archive/25_bootstrap_flow-next-steps.md`.

## Next
1. **(Opus/Architect) Plan Phase 6.** Read the "Phase 6 — Collapse the flags"
   sketch section of `docs/migration_roadmap.md`. The goal: remove the proven-
   redundant `classic`/`langgraph`/`mcp`/`ralph`/`declarative`/`isolation`
   scaffolding once each new path is proven, so the codebase stops carrying
   untested cross-products and a confusing dual surface. Run a planning pass
   (one question at a time, HITL gates) → write the first Phase 6 `sprint_plan.md`.
2. Watch the sequencing constraint the roadmap already flags: CLI unification
   onto MCP (`resume --from-issue`) and `run_loop` deletion gate parts of the
   flag collapse — sequence those explicitly in the plan.

## HITL gate
**CLOSED** — Sprint 25 review is complete and approved; nothing awaiting review.

## Carry-forward
- **Sprint-25 review nit:** two vacuous "no open_pr" assertions
  (`tests/flows/bootstrap/test_flow.py:109`, `test_integration.py:110`) — cosmetic,
  fold into an opportunistic cleanup.
- **Sprint-24 review nit (still open):** no unit test over
  `flows/maintenance.flow._default_run_tests`.
- **22b nit (still open):** bare `python` vs `sys.executable` in the committed
  `loop_engine.mcp.json` github stanza.
- All three are orthogonal to Phase 6; pick up opportunistically.

## Pointers
- `docs/migration_roadmap.md` — Phase 5 done; ▶ NEXT ACTION → plan Phase 6.
  The "Phase 6 — Collapse the flags" section is the sketch to expand.
- `.ai/context/workflow.md` — the Opus↔Sonnet handoff protocol + switch points.

## Working tree
- Clean at HEAD `659d32a` before this archival. The archival commit (this
  `.ai/` cursor advance + roadmap update) still needs to be committed.
