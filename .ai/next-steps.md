# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 6 — Collapse the flags — the host-gated flip block
(`27_phase6_flip_block`) — `planning`.** Next session is **Opus/Architect**,
writing the plan. No HITL gate open. Note: the *implementation* of this block is
gated on a daemon-bearing host for live verification — the planning pass can
proceed now, but the code lands only once the host is available.

## Just done (Opus/Architect — Sprint 26 review + close-out)
- **HITL-reviewed Sprint 26 (`3a9bc30`/`b7e2496`) at high effort** (8-angle
  `/code-review` + manual trace) → **APPROVED**. No default-path defect; suite
  green; conventions/boundary posture intact (keyring-free, four subprocess
  surfaces, three-way disjoint verb sets, no `State` change).
- **Recorded findings R1–R7** in `docs/migration_roadmap.md` (Sprint 26 HITL
  subsection) + `sprints/DEFERRED_VERIFICATION.md` §9 — all deferred, none
  block approval; the seam-shaped ones (R1–R4, R7) fold into this flip block,
  R5/R6 (pre-existing `resume` abort crash + first-block-only answer parse) are
  independent fixes.
- **Archived Sprint 26**: snapshotted its cursor to
  `.ai/archive/26_issue_io_mcp_unification-next-steps.md`, updated the roadmap
  status row + NEXT ACTION, advanced `.ai/state.json` to `27_phase6_flip_block`.

## Next
1. **(Opus/Architect) Plan the host-gated Phase 6 flip block.** Scope (roadmap
   "Collapse the flags"): flip defaults + delete classic paths behind the four
   sunsettable flags (`LOOP_ENGINE_ENGINE=langgraph`, `TOOLS=mcp`,
   `CODER=ralph`, `PERSONAS=declarative`; keep `ISOLATION`); the dual-field
   `artifacts`/`artifact_refs` strip (bump `schema_version` + extend
   `migrate_state_payload`); the `loops/default/loop.py` flag-branch collapse;
   and the issue-path default-flip/classic-deletion **carrying Sprint 26's
   R1–R7**. Resolve the two open planning-pass questions: per-flag vs
   one-big-run verification bar, and whether any flag survives as a documented
   break-glass. Deliver as `sprints/27_phase6_flip_block/sprint_plan.md`.
2. Implementation waits on a daemon-bearing host (live verification per
   `DEFERRED_VERIFICATION.md`).

## HITL gate
**CLOSED.** Sprint 26 approved + archived. The next unit is a fresh Opus
planning pass — no gate open.

## Pointers
- `docs/migration_roadmap.md` — "Phase 6 — Collapse the flags" (the flag-fate
  table + "Also collapses here") and the "Sprint 26 … HITL review" subsection
  (R1–R7).
- `sprints/DEFERRED_VERIFICATION.md` — §9 (issue-server live round-trip + the
  R1–R7 routing into the flip).
- `sprints/27_phase6_flip_block/sprint_plan.md` — **to be written** by the next
  planning pass.
- `.ai/context/workflow.md` — the Opus↔Sonnet handoff protocol.

## Working tree
- HEAD `b7e2496` (Sprint 26). Uncommitted: the review-recording + archival
  changes (`docs/migration_roadmap.md`, `sprints/DEFERRED_VERIFICATION.md`,
  `.ai/state.json`, `.ai/next-steps.md`) — commit these to make the archival
  durable.
