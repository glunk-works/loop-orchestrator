# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 5 — Sprint 23 (`trigger_surface`) — `implementing`.**
The Opus/Architect planning pass is done and HITL-approved; the plan is written.
Next is a Sonnet/Coder implementation session against the sprint file.

## Just done (Opus/Architect — 23 planning pass)
- **Planned Sprint 23 — the trigger surface** (Phase 5 piece 2): a FastAPI webhook
  server that turns an `agent-action` label / `/agent-run` comment into a real
  default-loop run via an injectable `RunDispatcher` seam. Delivered as
  `sprints/23_trigger_surface/sprint_plan.md` (6 tasks).
- **Settled six gating decisions** (one question at a time, HITL-gated), all
  recorded in the plan's Context block: capability slice (dispatch the existing
  default loop; no factory-flow wiring); **in-process** worker-thread dispatch =
  **no 4th subprocess surface**; **FastAPI pinned, uvicorn deferred** (hermetic
  `TestClient`); **HMAC over raw body, env-var secret, fail-closed**; unified
  `human_input` = issue title+body, bare trigger verbs, all else a 2xx no-op;
  new `src/loop_engine/trigger/` package (no keyring, no writes, no subprocess).

## Next
1. **(Sonnet/Coder) Implement Sprint 23** — Tasks 1–6 in order per
   `sprints/23_trigger_surface/sprint_plan.md`: shared `runner.py` refactor →
   `RunRequest`+parser → `RunDispatcher`+`InProcessDispatcher` → FastAPI app →
   boundary static test + hermetic e2e → deps/SBOM/docs/roadmap. Run the green
   gate (test/lint/format/audit/sbom) per task; **regenerate `sbom.json`** (first
   web dependency).
2. **Then handoff to Opus** for HITL review of the diff.

## Carry-forward
- **Do NOT scope-creep into the factory flows** — no `tools/repo_io` call, no
  clone, no branch/PR, no `git push` surface. The maintenance flow (piece 3,
  Sprint 24) owns the deferred local-git subprocess-surface decision.
- **First web dependency** — pin FastAPI (pydantic-2.13-compatible, audit-green);
  `httpx` is dev/test only (TestClient), not runtime; regenerate + commit `sbom.json`.
- **Open low nit (carried from 22b):** bare `python` vs `sys.executable` in the
  committed `loop_engine.mcp.json` github stanza — pick up if convenient.

## Pointers
- `sprints/23_trigger_surface/sprint_plan.md` — the active task list (6 tasks) +
  locked decisions. Read the Context block before starting.
- `docs/migration_roadmap.md` — Phase 5 "Scope" (four pieces); ▶ NEXT ACTION
  advances to Sprint 24 (maintenance flow) once 23 lands (Task 6).
- `.ai/context/workflow.md` — the Opus↔Sonnet handoff protocol + switch points.

## Working tree
- Sprint 23 plan is uncommitted (`sprints/23_trigger_surface/` untracked) on
  `feat/mcp-langgraph-migration`. Commit it **with** this handoff cursor as one
  unit (the 22b precedent `5a3d488` bundles "HITL-approved plan + handoff").
