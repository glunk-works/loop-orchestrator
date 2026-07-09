# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 5 — Sprint 24 (`maintenance_flow`) — `implementing`.**
The plan is written and HITL-approved (Opus planning pass, this session). The next
session is **Sonnet/Coder** implementing tasks 1–6.

## Just done (Opus/Architect — Sprint 24 planning pass)
- **Ran the Sprint 24 planning pass** (one question at a time, HITL gates) and locked
  the four dominant decisions:
  1. **Scope = capability slice** (mirrors 22b/23) — no CLI, no trigger wiring, no bootstrap flow.
  2. **Git-write surface = a NEW `tools/git_io` module** — honestly the **4th** sanctioned
     subprocess surface (not bolted onto `repo_io`=gh or `worktree`=orchestrator-own).
  3. **Exec model = injectable `RunStep` seam → `runner.run_in_tree`** (default loop, cwd
     pinned to the clone, **no** `worktree_run`); "absorb" = run in the clone's cwd.
  4. **Green gate = `coder_tools` pytest on the clone; green-ONLY push+PR against `develop`;
     red ⇒ no push/PR**; auto-merge stays impossible (`open_pr` terminal, no merge verb).
- **Wrote `sprints/24_maintenance_flow/sprint_plan.md`** — 6 tasks, Context section records
  all four locked decisions ("do not re-open").

## Next
1. **(Sonnet/Coder) Implement Sprint 24, tasks 1–6 in order** per the sprint plan. Do NOT
   re-open the locked decisions. Green gate each task; **`sbom.json` unchanged** (no dep added).
2. `/handoff` back to **Opus/Architect** for HITL review of the Sprint 24 diff when green.
3. `/archive-sprint` only after the review is clean and committed.

## Carry-forward
- **Open low nit (carried from 22b, still unresolved):** bare `python` vs `sys.executable`
  in the committed `loop_engine.mcp.json` github stanza — orthogonal to this flow, not touched in 24.

## Pointers
- `sprints/24_maintenance_flow/sprint_plan.md` — **the task list for this sprint** (read first).
- `docs/migration_roadmap.md` — Phase 5 status; ▶ NEXT ACTION → Sprint 24 (maintenance flow).
- `sprints/22b_native_github_server/`, `sprints/23_trigger_surface/` — the foundation (repo_io
  factory verbs) + precedent (top-level caller + injectable seam + boundary test) 24 builds on.
- `.ai/context/workflow.md` — the Opus↔Sonnet handoff protocol + switch points.

## Working tree
- **Clean.** The plan + this cursor are committed on the handoff commit at HEAD
  (tracked files: `sprints/24_maintenance_flow/sprint_plan.md`, `.ai/next-steps.md`);
  `.ai/state.json` is the git-ignored machine cursor and pins the exact `last_commit`.
