# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 5 — Sprint 23 (`trigger_surface`) — `planning`.**
Sprint 22b (github MCP server capability slice) is complete, reviewed, and
archived. Next up is an Opus/Architect **planning pass** for the trigger
surface — Phase 5 piece 2. No plan written yet.

## Just done (Opus/Architect — 22b close-out)
- **HITL review of 22b** (`7b46227`): approved with one required finding —
  `_validate_clone_dest` gated its symlink-escape check on `path.exists()`,
  letting the normal clone case (non-existent target under a symlinked parent)
  escape the run tree. **Fixed** in review-fix commit `5bc3811` + regression
  test; green gate 426 passed. Low nit (bare `python` vs `sys.executable` in the
  committed `loop_engine.mcp.json`) deferred.
- **Archived 22b** — cursor snapshotted to
  `.ai/archive/22b_native_github_server-next-steps.md`; roadmap status row +
  NEXT ACTION advanced; `.ai/state.json` moved to Sprint 23 / `planning`.

## Next
1. **(Opus/Architect) Plan Sprint 23 — the trigger surface.** A FastAPI webhook
   server that triggers a graph run on a GitHub issue labeled `agent-action`
   (or a slash command in an issue comment) — roadmap Phase 5 "Scope" piece 2
   (`docs/migration_roadmap.md:346`). Piece 1 (github server) landed in 22b, so
   this is the first step toward the maintenance flow (piece 3) + bootstrap flow
   (piece 4) that actually call the github factory verbs. Planning pass: one
   question at a time, HITL gates; deliver `sprints/23_trigger_surface/sprint_plan.md`.
2. **Then handoff to Sonnet** for implementation.

## Carry-forward
- **Deferred (22b → maintenance flow):** the local-git subprocess surface
  (`git push` inside a cloned tree) belongs to the maintenance flow, not the
  trigger surface — don't introduce it in Sprint 23.
- **Open low nit:** bare `python` vs `sys.executable` in the committed
  `loop_engine.mcp.json` github stanza — pick up if convenient.

## Pointers
- `docs/migration_roadmap.md` — Phase 5 "Scope" (four pieces) + "sprint
  decomposition"; the ▶ NEXT ACTION line now points at Sprint 23 planning.
- `sprints/23_trigger_surface/sprint_plan.md` — **to be written** (this planning pass).
- `.ai/context/workflow.md` — the Opus↔Sonnet handoff protocol + switch points.

## Working tree
- 22b review-fix committed at `5bc3811` on `feat/mcp-langgraph-migration`. The
  archival edits (this cursor + roadmap) are uncommitted — commit them to make
  the archive durable.
