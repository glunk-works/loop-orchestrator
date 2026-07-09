# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 5 — Autonomous triggers + multi-repo factory — `planning`.** **All of Phase 4
is now built, reviewed, and its review findings resolved** (parts 1, 1a, 2). Phase 5
is currently **sketch-only** in the roadmap; the next session's job is the planning
pass (decompose it into sprint(s) and write the first `sprint_plan.md`). No HITL gate open.

## Just done
- **Phase 4 · part 1a (sprint 19a, `d675d5d`) HITL-reviewed → 3 findings resolved in
  `684cc92`:** `_upsert_task_section` `### `-in-body orphaning (correctness), `_repair`
  false-success ledger, and dependency name-matching precision (tightened to distinctive
  underscore-bearing tokens). All flag-scoped to `LOOP_ENGINE_CODER=ralph`. This closes
  Phase 4 entirely.
- **Sprints 20 (`cf48b0c`) + 21 (`aceb23a`, `03818d9`) archived** (part 2: declarative
  `GeneratorNode` personas + PM `CriticGate`; 3 review findings resolved in `03818d9`).
  Sprint 21 cursor snapshotted to `.ai/archive/21_declarative_review_fixes-next-steps.md`.
  (Sprint 20 predates the `.ai/` layer — no cursor to snapshot; its record lives in the
  roadmap + `sprints/20_declarative_generators/` + git.)

## Next
1. **(Opus / Architect) Plan Phase 5** — autonomous triggers (FastAPI webhook
   triggers) + the multi-repo factory. Planning pass, **one question at a time**,
   HITL-gated. Read the roadmap's Phase 5 sketch first, then decompose into
   sprint(s) and write `sprints/NN_*/sprint_plan.md`.
2. **Cross-cutting deferrals still open** (roadmap "Cross-cutting follow-ups"): #4
   Ralph cap-exhaustion → escalate-not-fail, and #5 the live-host Ralph convergence/cost
   verification (`sprints/DEFERRED_VERIFICATION.md`). Neither blocks Phase 5 planning.

## Pointers
- `docs/migration_roadmap.md` — deep status + decisions log; see the "Phase 5 —
  Autonomous Triggers & Multi-Repo Factory" section (sketch) and the ▶ NEXT ACTION line.
- `sprints/` — no Phase 5 sprint_plan yet; it's the first planning deliverable.
- `.ai/archive/21_declarative_review_fixes-next-steps.md` — the retired sprint-21 cursor.
- `.ai/context/workflow.md` — the Opus↔Sonnet handoff protocol + switch points.
