# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 6 — sprint `27_phase6_flip_block` — `planned_host_gated`.**
The flip block is **already planned**; it cannot proceed in this devcontainer.
Its one blocking obligation is the **re-attempt of V2** — a real
container-sandboxed Ralph run reaching terminal `COMPLETED` within budget on a
daemon-bearing host. All in-code blockers are now closed. **V2 held OPEN.**

## Just done (Opus/Architect, 2026-07-11)
- **Sprint 30 (`ralph_test_scope`) COMPLETE + archived.** Closed
  **F-RALPH-OVERSPEC-TEST** (V2 re-attempt #6's finding: Ralph authored
  out-of-spec tests asserting private/underscore internals, then escalated on
  their self-caused failures instead of self-fixing). T1 (`551338a`) added the
  test-scope guardrail to the shared `PROMPT_TEMPLATE` and the
  self-fix-before-escalate guardrail to Ralph's per-increment prompts
  (prompt-only, locked FD1/FD2 — no gate-guard). T2 (`f934fda`) reconciled
  `sprints/DEFERRED_VERIFICATION.md`. HITL-reviewed by Opus and approved this
  session: diff scoped to exactly the planned 5 files (no engine/gate/`State`
  changes), targeted + full suite (580 passed) and lint independently
  re-verified green. Cursor snapshot archived to
  `.ai/archive/30_ralph_test_scope-next-steps.md`.
- Updated `docs/migration_roadmap.md` (Phase 6 row + NEXT ACTION) to record
  sprint 30 and re-scope V2's remaining gate to the host observation only.

## Next
1. **Sprint 27 V2 re-attempt (host, Opus) — the critical path, HOST-GATED.** On a
   daemon-bearing host (DinD + `gh` auth + `loop-engine-dev:latest`), under
   `LOOP_ENGINE_ISOLATION=container` (+ `ENGINE=langgraph TOOLS=mcp
   PERSONAS=declarative CODER=ralph`), reuse the run-#6 staging recipe (harness
   `scratch/v2_run_harness.py`, tree `scratchpad/v2_tree`, injected
   `issue_filer`, absolute env python) and observe terminal `COMPLETED` within
   budget. Do NOT mark V2 PASS until literally observed. A re-run that still
   escalates on a self-authored test means the prompt-only fix was
   insufficient — escalate to the deferred gate-guard (FD1 in
   `sprints/30_ralph_test_scope/sprint_plan.md`), don't just re-tweak wording.
2. **On V2 PASS:** the subtractive sprint 27 flag deletions unblock (remove
   `ENGINE`/`TOOLS`/`PERSONAS` classic paths + `artifacts` strip + `loop.py`
   collapse + the issue-path default-flip carrying Sprint 26 findings R1–R7;
   Task 4 `CODER=ralph` gated on V2).
3. **If no host is available this session:** there is **no in-devcontainer work
   on the critical path** — consider pulling a backlog item instead
   (`docs/backlog.md` BL-1..BL-5).

## HITL gate
No outstanding review owed — Sprint 30 fully approved. The open gate on the
critical path is the **sprint 27 V2 host observation** (a real
container-sandboxed `COMPLETED`), host-gated and not satisfiable in this
devcontainer. V3 not started. Sprint 27's flag-deletion tasks stay gated on
V2 (and V3) passing.

## Pointers
- `sprints/27_phase6_flip_block/sprint_plan.md` — the flip block (planned, host-gated); its V2 is the held-open `COMPLETED` obligation.
- `sprints/30_ralph_test_scope/sprint_plan.md` — the prompt-only F-RALPH-OVERSPEC-TEST fix (complete, archived).
- `sprints/DEFERRED_VERIFICATION.md` — V1 PASS(qualified); **V2 OPEN** (host re-attempt only, all in-code blockers closed); V3 not started.
- `docs/migration_roadmap.md` — Phase 6 row + NEXT ACTION (updated for sprint 30).
- `docs/backlog.md` — BL-1..BL-5.

## Working tree
- HEAD `5c96e15`. Sprint 30 fully committed + pushed (`551338a`, `f934fda`).
  This archival session's delta (`.ai/next-steps.md` reseed, `.ai/archive/`
  snapshot, `docs/migration_roadmap.md` update) is uncommitted — commit it to
  make the archival durable. Untracked `scratch/` (V2 specs/run logs/harness)
  remains out of all commits — not for commit. `.ai/state.json` is git-ignored
  (local mirror only).
