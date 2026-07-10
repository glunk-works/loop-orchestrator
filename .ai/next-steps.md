# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 6 — Collapse the flags — the host-gated flip block
(`27_phase6_flip_block`) — `blocked_pending_planning`.** The host verification
runs (V1/V2) ran and surfaced a **blocking finding, F-GATE-SANDBOX**: no run can
reach `COMPLETED` under `LOOP_ENGINE_ISOLATION=container` because the Coder gates'
verification pytest is not sandboxed. A **planning/sequencing decision (Opus/
Architect)** is required before any more host runs or deletions. **HITL gate OPEN
(planning).**

## Just done (Opus/Architect — host verification session, 2026-07-10)
- **V1 (ENGINE+TOOLS+PERSONAS) — PASS (qualified).** 4 real runs in target config
  (`langgraph`+`mcp`+`declarative`+`container`). All three flags verified functional
  + parity through PM→Arch→Sprint + the in-container MCP coder tool loop (25–33
  sandboxed tool calls/run) + the escalation/pause/snapshot ladder. Cost ~$0.38/run
  upstream. **Terminal `COMPLETED` not observed** — the classic `CoderIacPersona`
  escalated in all 4 (worktree-of-self collision; the `docs/sprints/src`
  artifact-write allowlist vs. generated root-file tasks; multi-sprint
  file-application; over-escalation) — all **orthogonal to the three flags** and
  identical on a classic run. Recorded in `sprints/DEFERRED_VERIFICATION.md`.
- **User decision:** classic `CoderIacPersona` is being **fully retired/replaced by
  Ralph** — don't invest in making the classic Coder reach `COMPLETED`.
- **V2 (Ralph) — BLOCKED on finding F-GATE-SANDBOX.** Ralph's algorithm engaged
  correctly (manifest emitted, `.agent/STATE.md` checklist, checked off
  `01_input_validation_foundation::t01`, 11 sandboxed tool calls) but the run
  crashed at the gate: `core/coder_gate.py::_raise_if_sandboxed` raises under
  `container`/`sandbox` isolation because the gate's verification pytest runs
  in-process (deferred sprint-18 work; the `run_tests` *tool* was sandboxed in
  Phase 3b, the gate's *own* pytest was not). **Neither Coder can reach ACCEPT →
  `COMPLETED` under container isolation** — this gates all of V1(terminal)/V2/V3.
- **Non-migration items** (from the repo owner): confirmed GPG signing works via a
  forwarded host agent (do NOT add the passphrase to infisical — it stays
  host-side; rebuild lever is `gpg-forward.sh`); added `docs/backlog.md` (BL-1
  in-loop Architect/QA code-review stage, BL-2 Slack) — committed `9072b41`.

## Next
1. **PLANNING DECISION (Opus/Architect) — sequencing around F-GATE-SANDBOX:**
   - **Option A — build the gate-sandbox wiring first:** route the Coder/Ralph
     gate's verification pytest through the MCP container sandbox (mirror Phase 3b's
     `run_tests` sandboxing; finishes Phase 3b), THEN run V1(complete)/V2/V3 under
     container. Makes the container end-state completable before any deletion.
   - **Option B — decouple deletions from the gate gap:** the three V1-target flags
     are already verified functional+parity through the in-container MCP tool loop;
     the gate refusal is flag-invariant. Consider proceeding with Tasks 1–3
     (ENGINE/TOOLS/PERSONAS) on that decomposed evidence, tracking the
     terminal-`COMPLETED`/container-gate proof as its own gate, and holding
     `CODER`/Ralph Task 4 until V2 + the gate wiring land.
   - See `sprints/DEFERRED_VERIFICATION.md` → "Finding F-GATE-SANDBOX" for the full
     write-up + evidence.
2. **Do NOT run more budget-spending host runs** until sequencing is decided.
3. **Commit the characterization** if not already: `sprints/DEFERRED_VERIFICATION.md`
   + this `.ai/next-steps.md` are uncommitted on the working tree.

## HITL gate
**OPEN (planning).** The sequencing decision (A vs B) is an Architect judgement
call. No deletion task lands until sequencing is chosen AND its gating V-run is
recorded PASSED. F-GATE-SANDBOX blocks any container-isolated `COMPLETED`.

## Pointers
- `sprints/DEFERRED_VERIFICATION.md` — V1/V2/V3 host-run results + **finding
  F-GATE-SANDBOX** (the blocking gate-sandbox gap + the A/B sequencing options).
- `src/loop_engine/core/coder_gate.py::_raise_if_sandboxed` — the container-isolation
  gate refusal (lines ~31–43).
- `sprints/27_phase6_flip_block/sprint_plan.md` — the flip-block plan (Task 0,
  V1–V3, Tasks 1–9) + FD1/FD2.
- `docs/migration_roadmap.md` — "Phase 6 — Collapse the flags".
- `docs/backlog.md` — BL-1 (in-loop Architect/QA review), BL-2 (Slack).

## Working tree
- HEAD `9072b41` (`docs: add product backlog`). **Uncommitted:**
  `sprints/DEFERRED_VERIFICATION.md` (V1/V2/V3 results + F-GATE-SANDBOX) and this
  `.ai/next-steps.md` regeneration (`.ai/state.json` is git-ignored). Commit before
  switching sessions so `/resume` sees a clean tree. Scratch verification logs live
  under `scratch/` (untracked, do not commit).
