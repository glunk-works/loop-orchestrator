# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 6 — sprint `27_phase6_flip_block` — `planned_awaiting_host_verification`.**
The flip block is fully planned; its Phase-3b-completion prerequisite (sprint 28)
is done, HITL-approved, and archived. What remains is **host-gated** — the flip
block does **not** start on a laptop.

## Just done (Opus/Architect — HITL review + archive, 2026-07-10)
- **Sprint 28 (gate-pytest sandbox) HITL review: PASSED.** Verified the
  gate-isolation invariant against the real code — no silent in-process fallback
  under sandbox modes, no fifth subprocess surface, `tools/mcp` import scoped to
  `coder_gate.py`. Two minor findings fixed in review-fix `386c660`: (1) enforce
  the in-process gate cwd contract (`run_gate_pytest` raises if `cwd != Path.cwd()`
  on the unsandboxed path instead of silently running a divergent tree); (2) test
  that an `MCPToolError` propagates rather than being parsed into a bogus gate
  decision. Full suite **563 passed**, lint/format clean; no dep/sbom change.
- **Sprint 28 archived** (`.ai/archive/28_gate_pytest_sandbox-next-steps.md`);
  roadmap Phase 3b + Phase 6 rows + NEXT ACTION updated to record it done.

## Next
1. **HOST-GATED verification (Opus/Architect, human-operated).** On a
   daemon-bearing host (real `gh` auth, container runtime, real Anthropic key,
   real API budget + real GitHub side effects):
   - **V1** — one big end-to-end factory run in the target production config
     (`ENGINE=langgraph` + `TOOLS=mcp` + `PERSONAS=declarative` +
     `ISOLATION=container`, classic Coder), parity-checked vs the classic
     baseline. Clears `ENGINE`/`TOOLS`/`PERSONAS`.
   - **V2** — a dedicated multi-sprint `CODER=ralph` convergence + cost run (no
     parity oracle). Clears `CODER=ralph`.
   - (**V3** — forced issue-escalation round-trip — gates only Task 8.)
   These are **not** a pytest gate. Record each PASS in `DEFERRED_VERIFICATION.md`.
2. **Only then** the subtractive deletions (Tasks 0–8): tag `pre-phase6-classic`
   (Task 0) → flip defaults + delete classic paths in `run_loop`-first order.
   **No deletion task lands before its gating V-run is recorded PASSED** (FD1/FD2).
3. **Do NOT run deletions on a laptop**, and do NOT keep any flag as a live
   break-glass — git (`pre-phase6-classic` tag + `git revert`) is the recovery
   mechanism.

## HITL gate
**None open for sprint 28** (review passed, archived). Sprint 27's deletions are
gated on their V-runs being recorded PASSED on a host — unblocked in code by
sprint 28, but the host proof (V1/V2/V3) has not yet been executed.

## Pointers
- `sprints/27_phase6_flip_block/sprint_plan.md` — the flip block (V1–V3 + Tasks 0–8,
  FD1/FD2 decisions, the "verification gates the deletions" discipline).
- `sprints/DEFERRED_VERIFICATION.md` — F-GATE-SANDBOX resolved-in-code (sprint 28);
  §3 sandboxing half CLOSED, per-task test-selection half still OPEN; V1/V2/V3 to
  be recorded here.
- `docs/migration_roadmap.md` — Status table (Phase 3b + Phase 6 rows) + NEXT
  ACTION, all updated for sprint 28.
- `.ai/archive/28_gate_pytest_sandbox-next-steps.md` — sprint 28 final cursor.
- `docs/backlog.md` — BL-1 in-loop review, BL-2 Slack, BL-3 prompt-caching review.

## Working tree
- HEAD `386c660` (sprint 28 review-fix). The archival changes (this
  `next-steps.md` + `docs/migration_roadmap.md`; `.ai/state.json` is git-ignored)
  are uncommitted — commit them to make the archival durable. Untracked `scratch/`
  is unrelated.
