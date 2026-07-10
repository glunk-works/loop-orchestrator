# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 6 — Collapse the flags — the host-gated flip block
(`27_phase6_flip_block`) — `blocked`.** The planning pass is **complete**: the plan
is written and both open questions are resolved + locked. Nothing else can proceed
offline — the whole block is gated on a **daemon-bearing host** for live
verification. No HITL gate open.

## Just done (Opus/Architect — flip-block planning pass)
- **Wrote the flip-block plan** → `sprints/27_phase6_flip_block/sprint_plan.md`:
  Task 0 (tag `pre-phase6-classic`), V1–V3 (host verification runs), Tasks 1–9
  (the flips/deletions in `run_loop`-first dependency order, ending in deleting
  `DEFERRED_VERIFICATION.md`). Each task names concrete files/symbols + per-
  deletion green-commit acceptance criteria; the issue-path flip (Task 8) carries
  Sprint 26's R1–R7.
- **Resolved + locked the two open planning questions** (recorded in
  `docs/migration_roadmap.md` "Open questions — RESOLVED"):
  - **FD1** — verification bar = per-flag *criterion*, batched *execution*: one
    big factory run clears ENGINE+TOOLS+PERSONAS; Ralph (§3) and the issue path
    (§9) carved out as dedicated runs; deletion in `run_loop`-first order.
  - **FD2** — no flag survives as a break-glass; tag the pre-deletion commit as
    the git recovery mechanism; `LOOP_ENGINE_ISOLATION` stays as genuine config.

## Next
1. **BLOCKED — waiting on a daemon-bearing host.** No offline work remains for
   this block.
2. **On the host (Opus/Architect judgement):** run the three verification gates —
   **V1** one big factory run (ENGINE+TOOLS+PERSONAS, parity-checked), **V2**
   Ralph convergence/cost (§3), **V3** forced issue-escalation round-trip (§9) —
   recording PASS/FAIL in `DEFERRED_VERIFICATION.md`.
3. **After a gate is PASSED (Sonnet/Coder):** execute the deletion Task(s) it
   gates, each a green reviewable commit, in the `run_loop`-first order (Task 0
   tag first → 1 ENGINE → 2 TOOLS → 3 PERSONAS → 4 CODER=ralph → 5 artifacts
   strip v3→v4 → 6 loop.py collapse → 7 docs → 8 issue-path flip (R1–R7) → 9
   delete `DEFERRED_VERIFICATION.md`). **No deletion before its gating V-run is
   PASSED.** Opus HITL-reviews per deletion/group.

## HITL gate
**CLOSED.** Planning complete; no gate open. Gates re-open only on the host (per-
deletion Opus review, each gated on its V-run passing first).

## Pointers
- `sprints/27_phase6_flip_block/sprint_plan.md` — the flip-block plan (Task 0,
  V1–V3, Tasks 1–9) + locked FD1/FD2 context.
- `docs/migration_roadmap.md` — "Phase 6 — Collapse the flags": the flag-fate
  table + "Open questions — RESOLVED" (FD1/FD2).
- `sprints/DEFERRED_VERIFICATION.md` — §3 (Ralph/V2), §9 (issue/V3); V1 is the
  ENGINE+TOOLS+PERSONAS big run.
- `.ai/context/workflow.md` — the Opus↔Sonnet handoff protocol.

## Working tree
- HEAD `c727a37`. Uncommitted: the new plan
  (`sprints/27_phase6_flip_block/sprint_plan.md`) + the roadmap FD1/FD2 edit
  (`docs/migration_roadmap.md`) + this handoff (`.ai/next-steps.md`,
  `.ai/state.json` — state.json is git-ignored). Commit these to make the plan
  durable before switching sessions.
