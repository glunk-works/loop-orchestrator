# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 6 — sprint `27_phase6_flip_block` — `planned_host_gated`.**
The flip block is **already planned**; it cannot proceed in this devcontainer.
Its one blocking obligation is the **re-attempt of V2** — a real
container-sandboxed Ralph run reaching terminal `COMPLETED` within budget on a
daemon-bearing host. All three *code* blockers are now closed. **V2 held OPEN.**

## Just done (Opus/Architect, 2026-07-11)
- **Sprint 29 (`coder_host_run_hardening`) COMPLETE + archived.** T1 F-TOOLLOOP-CAP
  (`b0be361`), **T2 F-CODER-NO-LINT (`10f27d3`) — HITL-reviewed by Opus + approved
  this session**, T3 doc reconciliation (`6b60467`). Cursor snapshot archived to
  `.ai/archive/29_coder_host_run_hardening-next-steps.md`.
- T2 review verdict: the `run_lint` ruff tool is correctly contained (fixed argv,
  `shell=False`, 60s timeout, `truncate_result`-capped, `resolve_tool_path`-validated,
  statically parses / never executes model code — strictly lower-risk than
  `run_tests`' pytest). 577 passed, lint/format clean, sbom unchanged; fifth
  sanctioned subprocess surface pinned in `test_subprocess_surfaces.py` + CLAUDE.md.
- Recorded F-TOOLLOOP-CAP + F-CODER-NO-LINT as resolved-in-code by sprint 29 in
  `DEFERRED_VERIFICATION.md`; re-titled V2 **OPEN (unblocked)**; updated the roadmap
  Phase 6 row + NEXT ACTION.

## Next
1. **Sprint 27 V2 re-attempt (host, Opus) — the critical path, HOST-GATED.** On a
   daemon-bearing host (DinD + `gh` auth + `loop-engine-dev:latest`), under
   `LOOP_ENGINE_ISOLATION=container` (+ `ENGINE=langgraph TOOLS=mcp
   PERSONAS=declarative CODER=ralph`), observe a real Ralph run reach terminal
   `COMPLETED` within budget. The **only** remaining prerequisite is
   **escalation-free staging** — a real remote or an injected non-crashing
   `issue_filer` so a stray escalation pauses cleanly instead of crashing
   `gh issue create` (the prior run converged 11 tasks but hit `BUDGET_EXCEEDED`
   one sprint short). Do NOT mark V2 PASS until literally observed.
2. **On V2 PASS:** the subtractive sprint 27 flag deletions unblock (remove
   `ENGINE`/`TOOLS`/`PERSONAS` classic paths + `artifacts` strip + `loop.py`
   collapse + the issue-path default-flip carrying Sprint 26 findings R1–R7).
3. **If no host is available this session:** there is **no in-devcontainer work on
   the critical path** — consider pulling a backlog item instead
   (`docs/backlog.md` BL-1..BL-5).

## HITL gate
No outstanding review owed — Sprint 29 fully approved + committed. The open gate on
the critical path is the **sprint 27 V2 host observation** (a real
container-sandboxed `COMPLETED`), host-gated and not satisfiable in this
devcontainer. Sprint 27's flag-deletion tasks stay gated on V2 (and V3) passing.

## Pointers
- `sprints/27_phase6_flip_block/sprint_plan.md` — the flip block (planned, host-gated); its V2 is the held-open `COMPLETED` obligation.
- `sprints/DEFERRED_VERIFICATION.md` — V1 PASS(qualified), **V2 OPEN (unblocked)**, V3 not started; F-GATE-SANDBOX closed by 28; F-TOOLLOOP-CAP + F-CODER-NO-LINT closed by 29.
- `docs/migration_roadmap.md` — Phase 6 row + NEXT ACTION (updated for sprint 29).
- `docs/backlog.md` — BL-1..BL-5.

## Working tree
- HEAD `6b60467` (sprint 29 T3). Sprint 29 fully committed.
  Untracked `scratch/` (V2 specs/run logs) remains out of all commits — not for commit.
  `.ai/state.json` is git-ignored (local mirror only). This regenerated
  `.ai/next-steps.md` + the sprint 29 doc changes are the committable dev-workflow
  delta.
