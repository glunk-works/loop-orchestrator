# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 5 — Autonomous triggers + multi-repo factory — `planning`.** Phase 4 · part 2
is complete, reviewed, and archived. Phase 5 is currently **sketch-only** in the
roadmap; the next session's job is the planning pass (decompose it into sprint(s)
and write the first `sprint_plan.md`). No HITL gate open.

## Just done
- **Sprints 20 (`cf48b0c`) + 21 (`aceb23a`, `03818d9`) archived.** Phase 4 · part 2
  (declarative `GeneratorNode` personas + PM `CriticGate`) is complete and reviewed;
  its three HITL-review findings were resolved in `03818d9`. Roadmap Status table +
  decisions log updated; sprint 21 cursor snapshotted to
  `.ai/archive/21_declarative_review_fixes-next-steps.md`.
- (Sprint 20 predates the `.ai/` workflow layer, so it had no cursor to snapshot —
  its record lives in the roadmap + `sprints/20_declarative_generators/` + git.)

## Next
1. **(Opus / Architect) Plan Phase 5** — autonomous triggers (FastAPI webhook
   triggers) + the multi-repo factory. Planning pass, **one question at a time**,
   HITL-gated. Read the roadmap's Phase 5 sketch first, then decompose into
   sprint(s) and write `sprints/NN_*/sprint_plan.md`.
2. **Still open elsewhere in Phase 4:** part 1a (`sprints/19a_ralph_hardening/`,
   `d675d5d`) is marked "awaiting HITL review" in the roadmap — confirm whether that
   review happened before treating Phase 4 as fully closed.

## Pointers
- `docs/migration_roadmap.md` — deep status + decisions log; see the "Phase 5 —
  Autonomous Triggers & Multi-Repo Factory" section (sketch) and the ▶ NEXT ACTION line.
- `sprints/` — no Phase 5 sprint_plan yet; it's the first planning deliverable.
- `.ai/archive/21_declarative_review_fixes-next-steps.md` — the retired sprint-21 cursor.
- `.ai/context/workflow.md` — the Opus↔Sonnet handoff protocol + switch points.
