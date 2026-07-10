# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 6 (via a Phase-3b-completion prerequisite) — sprint `28_gate_pytest_sandbox`
— `implementing`.** The F-GATE-SANDBOX sequencing decision is resolved (repo owner
chose **Option A** — build the gate-sandbox wiring first). Sprint 28 is **planned +
approved to implement**; next session is **Sonnet/Coder** executing its four tasks.

## Just done (Opus/Architect — planning session, 2026-07-10)
- **Sequencing decision: Option A.** Route the Coder gates' verification pytest
  through the MCP container sandbox (mirror Phase 3b's `run_tests` tool sandboxing)
  *before* running sprint 27's V-suite. Finishes Phase 3b; unblocks V1(complete)/V2/V3.
- **Wrote `sprints/28_gate_pytest_sandbox/sprint_plan.md`** (4 tasks). Locked design
  (user-confirmed): the isolation-aware dispatch lives in a **new `tools/mcp`
  helper** `run_gate_pytest(path, cwd)` (mirrors `_CoderToolBackend.resolve`), and
  `core/coder_gate.py` calls it + **deletes `_raise_if_sandboxed`** — the gate
  verifies inside the sandbox instead of refusing. Rejected the injected-seam
  alternative (heavier; the sandbox path must self-select on `sandbox_runtime_mode()`,
  not be an opt-in capability like Sprint 26's `issue_filer`).
- **Grounded the plan against real code:** the `core → tools/mcp` edge is
  convention-only (`tests/core/test_boundaries.py` pins only the persona rule — no
  test change); `run_tests` tests live in `tests/tools/test_coder_tools.py`; no new
  subprocess surface (the sandbox is launched by `stdio_client`, same as the tool
  path).
- **Backlog:** added **BL-3 — prompt-caching review** (correctness + improvement
  opportunities) to `docs/backlog.md` (repo owner ask).

## Next
1. **Implement sprint 28 (Sonnet/Coder)** — Tasks 1–4, each an independently
   committable green commit (see `sprint_plan.md` for the full spec):
   - **T1** factor `format_run_tests_result`/`parse_run_tests_result` in
     `tools/coder_tools/run_tests.py` (one source of truth for the result string).
   - **T2** add `run_gate_pytest(path, cwd)` to `tools/mcp` (in-process on
     `none`/`worktree`; `build_coder_tool_provider` dispatch under
     `container`/`sandbox`; existence-check sentinel orchestrator-side; **no** silent
     in-process fallback).
   - **T3** rewire both gates onto it; **delete `_raise_if_sandboxed`** + both call
     sites; add the `core → tools/mcp` edge + record it in `CLAUDE.md`.
   - **T4** update `DEFERRED_VERIFICATION.md`: F-GATE-SANDBOX resolved-in-code
     (host re-verification → sprint 27 V1/V2); keep the per-task-test-selection
     deferral open.
2. **Then `/handoff` → Opus HITL review** of the sprint 28 diff before it lands.
3. **Do NOT touch sprint 27 deletions** — they stay blocked until sprint 28 lands
   AND its gating host V-runs pass.

## HITL gate
Planning sequencing gate **RESOLVED** (Option A). **Open gate:** Opus HITL review of
the sprint 28 implementation diff (the gate-isolation invariant — no silent
in-process fallback under sandbox modes, no fifth subprocess surface — is
correctness-critical). Sprint 27's deletions remain gated on sprint 28 + host V-runs.

## Pointers
- `sprints/28_gate_pytest_sandbox/sprint_plan.md` — the active sprint (4 tasks + DoD).
- `sprints/DEFERRED_VERIFICATION.md` — finding **F-GATE-SANDBOX** (the gap 28 closes)
  + V1/V2/V3 host-run results.
- `src/loop_engine/core/coder_gate.py` — `_raise_if_sandboxed` (delete) +
  `_run_gate_pytest` (delegate to the new helper).
- `src/loop_engine/tools/mcp/provider.py` — `container_server_params` +
  `build_coder_tool_provider` (the tool-path sandbox the gate mirrors).
- `sprints/27_phase6_flip_block/sprint_plan.md` — the follow-on flip block (after 28).
- `docs/migration_roadmap.md` — Phase 3b row ("sandboxed gate pytest deferred") +
  "Phase 6 — Collapse the flags".
- `docs/backlog.md` — BL-1 in-loop review, BL-2 Slack, BL-3 prompt-caching review.

## Working tree
- HEAD `bd6b162`. **Uncommitted:** `docs/backlog.md` (BL-3), the new
  `sprints/28_gate_pytest_sandbox/` plan, and this `.ai/next-steps.md` regeneration
  (`.ai/state.json` is git-ignored). **Commit before switching sessions** so
  `/resume` sees `last_commit` == HEAD. Scratch logs under `scratch/` stay untracked.
