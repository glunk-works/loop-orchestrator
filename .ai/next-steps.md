# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 4 · part 2 (sprint `20_declarative_generators`) — `awaiting_hitl_review`.**
Also just landed: the dev-workflow scaffolding itself (this `.ai/` layer + skills).

## Just done
- Phase 4 · part 2 built + committed `cf48b0c` (roadmap hash recorded `75369ed`): declarative `GeneratorNode` personas + PM `CriticGate`, behind `LOOP_ENGINE_PERSONAS=declarative` (default `classic`). 385 tests green; lint/format/audit/sbom clean.
- Workflow optimization: lean `CLAUDE.md`, `.ai/` externalized-state layer, `/resume` `/handoff` `/archive-sprint` skills, Sonnet `coder` subagent, Opus/Sonnet routing (this change; commit pending).

## Next
1. **(Opus / Architect) HITL-review the Phase 4 · part 2 diff** (`cf48b0c`) — e.g. `/code-review`, confirm the parity claims + the flag-gated PM escalation-shape change. This is the open **HITL gate**.
2. On approval → `/archive-sprint` for sprint 20, then **plan Phase 5** (FastAPI webhook triggers + glunk-works multi-repo factory) — still sketch-only, needs its own planning pass (one question at a time).
3. Implementation of a planned sprint → hand off to a fresh **Sonnet** session (`/handoff` → `/resume`).

## Pointers
- `docs/migration_roadmap.md` — deep status + decisions log (resume point of record).
- `sprints/20_declarative_generators/sprint_plan.md` — the sprint just built.
- `.ai/context/workflow.md` — the Opus↔Sonnet handoff protocol + switch points.
