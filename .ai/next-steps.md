# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 6 — sprint `29_coder_host_run_hardening` — `awaiting_hitl_review`.**
Planned this session from two Phase-6 **V2 host-run findings**, both orthogonal to
the flip-block flags. **Task 1 is already implemented + green + uncommitted;**
Task 2 (the ruff tool) is specced for a Sonnet session. **V2 is held OPEN.**

## Just done (Opus/Architect — V2 host runs + planning, 2026-07-10)
- **Ran 4 real container-sandboxed V2 factory runs** (`langgraph+mcp+declarative+ralph+container`, $5 cap, Seuss27, throwaway src-only scratch tree). **Run #3 converged 11 tasks across 6 sprints** — whole `textkit` library written, **`truncate` converged**, container gate **ACCEPTed 11×** (F-GATE-SANDBOX host-verified live) — and terminated cleanly at `BUDGET_EXCEEDED` **one sprint short of `COMPLETED`**. Runs that **escalated** (spec ambiguity; Coder asking for `ruff` it can't run) crashed on the remote-less tree's `gh issue create`.
- **Two findings, both surfaced live:** **F-TOOLLOOP-CAP** (a stuck inner tool loop hit the 12-iteration cap and the uncaught `ToolLoopExceededError` crashed the run) and **F-CODER-NO-LINT** (the Coder can't run `ruff`, so a "ruff clean" criterion escalates on missing tooling).
- **Implemented Task 1 (F-TOOLLOOP-CAP) this session — GREEN, UNCOMMITTED:** graceful catch in `ralph.py` (→ no-output degradation) + `core/engine.py` (→ terminal `FAILED_STAGE`, mirroring `BudgetExceededError`); `DEFAULT_MAX_TOOL_ITERATIONS` **12→40** with the USD budget documented as the primary bound. `hatch run test` = **565 passed**, lint/format clean.
- **Planned sprint 29** (`sprints/29_coder_host_run_hardening/sprint_plan.md`); **backlogged BL-4** (Ralph loop watcher — progress/liveness detection vs. the blunt cap).

## Next
1. **Opus/Architect (immediate):** approve the sprint 29 plan; **HITL-review Task 1's uncommitted diff** (ralph.py + core/engine.py + client.py + the two test files); **commit Task 1** as its own change. HITL gate is OPEN here.
2. **Then `/handoff` → Sonnet session** to implement **Task 2 (F-CODER-NO-LINT)** — the `run_lint` Coder tool over `ruff check`/`ruff format --check`. This **adds a FIFTH sanctioned subprocess surface** → it must amend `tests/tools/test_subprocess_surfaces.py` + the CLAUDE.md "exactly four subprocess surfaces" contract, and grow the Coder tool-set to `{read_file,list_files,grep,run_tests,run_lint}`. Mandatory **Opus HITL review** after (new subprocess surface = security boundary). Then Task 3 (doc reconciliation).
3. **Then re-attempt V2 for a real `COMPLETED`** on a host — with the ruff tool removing the structural escalation, plus **escalation-free staging** (a real remote or an injected non-crashing `issue_filer` so a stray escalation pauses cleanly instead of crashing).

## HITL gate
**OPEN (Opus):** approve sprint 29 plan + review Task 1's already-green, uncommitted
diff before it lands. **V2 held OPEN** — do NOT record it PASS; the literal
container run→`COMPLETED` observation is still owed (gated on sprint 29 + staging).
Sprint 27 flip-block deletions remain gated on their V-runs.

## Pointers
- `sprints/29_coder_host_run_hardening/sprint_plan.md` — Task 1 (implemented-pending-review), Task 2 (run_lint tool), Task 3 (doc reconciliation); the four→five subprocess-surface amendment + security note (ruff parses, doesn't execute).
- `sprints/27_phase6_flip_block/sprint_plan.md` — the flip block; its V2 is the held-open `COMPLETED` obligation.
- `sprints/DEFERRED_VERIFICATION.md` — V1 PASS(qualified), **V2 OPEN**, V3 not started; F-GATE-SANDBOX closed by 28; F-TOOLLOOP-CAP/F-CODER-NO-LINT to be recorded by sprint 29 Task 3.
- `docs/backlog.md` — BL-1..BL-3 + **BL-4** (Ralph loop watcher).
- `docs/migration_roadmap.md` — Phase 6 row + NEXT ACTION.

## Working tree
- HEAD `e9fd22e`. **Uncommitted:** Task 1 fix (`core/engine.py`, `personas/coder_iac/ralph.py`, `tools/llm/client.py`, `tests/core/test_engine.py`, `tests/personas/test_ralph_coder.py`), `docs/backlog.md` (BL-4), and untracked `sprints/29_coder_host_run_hardening/`. Untracked `scratch/` holds the V2 specs + run logs (not for commit). Commit Task 1 (after review) before switching sessions so `/resume` sees a matching HEAD.
