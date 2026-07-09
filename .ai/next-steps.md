# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 5 — Sprint 24 (`maintenance_flow`) — `planning`.**
Sprints 23 + 23a are archived (23a re-reviewed clean, `212beeb`). No Sprint 24
plan exists yet — the next session is a fresh Opus/Architect planning pass.

## Just done (Opus/Architect — 23a re-review + archival)
- **HITL re-reviewed the Sprint 23a diff (`212beeb`)** via `/code-review` (high
  effort). Verdict: **clean** — all 3 prior findings correctly closed (task
  retention + done-callback, `400`-not-`500` on unparseable body, `_run`
  failure logging), and the non-object-JSON edge is already defended by
  `parse_event`'s `isinstance(payload, dict)` guard (routes to `204`).
- **Archived Sprints 23 and 23a.** Snapshotted the 23a cursor to
  `.ai/archive/23a_trigger_review_fixes-next-steps.md`; advanced `.ai/state.json`
  to Sprint 24 (`planning`, Opus/Architect); updated `docs/migration_roadmap.md`
  (status row + NEXT ACTION + Sprint 23 detail line now mark 23a landed +
  re-reviewed clean, commit chain extended to `212beeb`).

## Next
1. **(Opus/Architect) Plan Sprint 24 (maintenance flow).** Planning pass, one
   question at a time, HITL gates. Write `sprints/24_maintenance_flow/sprint_plan.md`.
   Scope (from carry-forward): the first caller to chain `tools/repo_io`'s factory
   verbs — clone -> feature-branch worktree -> absorb `CLAUDE.md`/`.agent/STATE.md`
   -> green gate -> push -> open PR against `develop`; **auto-merge stays prohibited**.
2. Resolve the **deferred local-git subprocess-surface decision** (`git push` in a
   cloned tree) as part of that plan — it would be a potential 4th sanctioned
   subprocess surface, so decide deliberately (reuse `tools/worktree`'s posture vs.
   a new fixed-argv `shell=False` surface).
3. `/handoff` to Sonnet/Coder once the plan is HITL-approved.

## Carry-forward
- **Open low nit (carried from 22b, still unresolved):** bare `python` vs
  `sys.executable` in the committed `loop_engine.mcp.json` github stanza.

## Pointers
- `docs/migration_roadmap.md` — Phase 5 status; ▶ NEXT ACTION → plan Sprint 24.
- `sprints/24_maintenance_flow/sprint_plan.md` — **to be written** (this sprint).
- `sprints/23_trigger_surface/`, `sprints/23a_trigger_review_fixes/` — the just-archived
  sprints (context for the trigger surface Sprint 24 builds on).
- `.ai/context/workflow.md` — the Opus↔Sonnet handoff protocol + switch points.

## Working tree
- **Clean.** The archival is committed as `5e99f1f` (tracked files:
  `.ai/next-steps.md`, `docs/migration_roadmap.md`); `.ai/state.json` and
  `.ai/archive/` are git-ignored local cursor files. HEAD == `last_commit`.
