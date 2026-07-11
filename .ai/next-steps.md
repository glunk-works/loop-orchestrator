# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 6 — sprint `30_ralph_test_scope` — planned, ready to implement (→ Sonnet/Coder).**
A prerequisite Ralph-hardening sprint that must land before sprint 27's V2 can pass.
Prompt-only fix (locked **FD1**, repo-owner-confirmed — no gate-guard).

## Just done (Opus/Architect host session, 2026-07-11)
- **V2 re-attempt #6** (daemon-bearing host, config `langgraph`+`mcp`+`declarative`+
  `ralph`+`container`) — **staging validated, but FAIL**: reached the container Ralph
  coder + full sandboxed tool loop, then escalated (`AWAITING_ISSUE`, $3.29/$5.00,
  run_id `0d5e3f3c…`). Injected non-crashing `issue_filer` paused cleanly (no `gh`
  crash) — the real-remote option was blocked (Seuss27 PAT scoped only to this repo).
- **Opened finding F-RALPH-OVERSPEC-TEST** — Ralph wrote correct code but authored an
  over-specified test (asserts private `_NON_ALNUM_RUN` via a broken import) then
  escalated instead of self-fixing. Closed the F-CODER-NO-LINT host obligation
  (rebuilt `loop-engine-dev:latest` **with ruff**).
- **Planned + committed + pushed** sprint 30 (prompt-only fix). Commits `01d4bdc`
  (V2 #6 delta) + `66bdb9c` (sprint 30 plan) — both **GitHub-Verified**.

## Next
1. **Sonnet implements sprint 30** — T1 (test-scope guardrail in `PROMPT_TEMPLATE` +
   self-fix-before-escalate guardrail in Ralph's per-increment prompts, with unit
   tests) and T2 (reconcile F-RALPH-OVERSPEC-TEST to resolved-in-code). Each an
   independently-committable green change with an **Opus HITL review** gate.
2. **Then a fresh V2 re-attempt** (host, Opus) — reuse the run-#6 staging recipe
   (harness `scratch/v2_run_harness.py`, tree `scratchpad/v2_tree`,
   `LOOP_ENGINE_DEV_IMAGE=loop-engine-dev:latest`, injected filer, absolute env
   python). Only this host `COMPLETED` *verifies* F-RALPH-OVERSPEC-TEST + discharges V2.
3. **On V2 PASS:** sprint-27 flag deletions unblock (Task 4 `CODER=ralph` gated on V2).

## HITL gate
None owed — nothing awaiting review. Open critical-path gates (host): V2 `COMPLETED`
(gated on the sprint-30 fix) and V3 (not started). No sprint-27 deletion lands until
V2 + V3 pass.

## Pointers
- `sprints/30_ralph_test_scope/sprint_plan.md` — the prompt-only fix (active sprint).
- `sprints/DEFERRED_VERIFICATION.md` — V1 PASS(qualified); V2 OPEN; F-RALPH-OVERSPEC-TEST
  OPEN (blocks V2→`CODER=ralph`); V3 not started.
- `sprints/27_phase6_flip_block/sprint_plan.md` — the flip block (host-gated).
- `docs/migration_roadmap.md` — Phase 6 row + NEXT ACTION.

## Working tree
- HEAD `66bdb9c` (pushed, Verified). Clean except untracked `scratch/` (V2
  specs/logs/harness/pubkey) + `scratchpad/v2_tree` — both out of all commits.
  `.ai/state.json` is git-ignored (local mirror only).
