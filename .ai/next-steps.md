# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 6 — Collapse the flags — the host-gated flip block
(`27_phase6_flip_block`) — `implementing`.** The host-provisioning block is
**CLEARED**: the DinD daemon is up, the dev image is built, `gh`/keyring are
restored, and the known-good `devcontainer.json` is committed. The next work is
the verification gates (Opus/Architect, budget-spending). No HITL gate open.

## Just done (Opus/Architect — host provisioning + security review)
- **Brought up the container runtime.** Second devcontainer rebuild landed the
  `containerUser: root` fix; `docker info` → `29.6.1` (daemon boots as root,
  dev session stays `app`). Built `loop-engine-dev:latest` and confirmed
  `import loop_engine` inside it.
- **Committed the known-good `devcontainer.json`** (`1449d65`) — DinD feature +
  `--privileged` + `containerUser: root`, with an inline JSONC scoping comment.
- **Security review of the privileged devcontainer.** No new *application* hole:
  the `--privileged`/`root` grants are confined to `.devcontainer/` and touch no
  enforced boundary. The untrusted-code boundary (inner isolation container:
  `--cap-drop ALL`, `no-new-privileges`, `--network none`, `--read-only`, single
  worktree bind) is unchanged and guarded by an exact-argv test
  (`tests/tools/test_sandbox_params.py`, 13 passed). The one real cost —
  `--privileged` widens the *outer* container's host-escape path — is documented
  as LOCAL-VERIFICATION-HOST-ONLY in the commit + the file.
- **Restored `gh`/keyring.** Auto-restore did NOT fire on the last rebuild
  (postStart didn't complete); re-ran `infisical-start.sh` (idempotent) → `gh`
  authenticated, keyring seeded. Root cause was the interrupted rebuild, not a
  script bug.

## Next
1. **Run the verification gates (Opus/Architect judgement, budget-spending).**
   First `export LOOP_ENGINE_DEV_IMAGE=loop-engine-dev:latest
   LOOP_ENGINE_ISOLATION=container`. Then **V1** (big ENGINE+TOOLS+PERSONAS
   factory run, parity-checked), **V2** (Ralph convergence/cost, §3), **V3**
   (forced issue-escalation round-trip, §9) — recording PASS/FAIL in
   `sprints/DEFERRED_VERIFICATION.md`.
2. **After a gate is PASSED (Sonnet/Coder):** execute the deletion Task(s) it
   gates, each a green reviewable commit, in `run_loop`-first order (Task 0 tag
   first → 1 ENGINE → 2 TOOLS → 3 PERSONAS → 4 CODER=ralph → 5 artifacts strip
   v3→v4 → 6 loop.py collapse → 7 docs → 8 issue-path flip (R1–R7) → 9 delete
   `DEFERRED_VERIFICATION.md`). **No deletion before its gating V-run is PASSED.**
   Opus HITL-reviews per deletion/group.
3. **If a future rebuild leaves `gh` unauthenticated:** re-run
   `sh /workspace/.devcontainer/infisical-start.sh` before V1.

## HITL gate
**CLOSED.** No gate open. Gates re-open on the deletion work (per-deletion Opus
review, each gated on its V-run passing first).

## Pointers
- `sprints/27_phase6_flip_block/sprint_plan.md` — the flip-block plan (Task 0,
  V1–V3, Tasks 1–9) + locked FD1/FD2 context.
- `docs/migration_roadmap.md` — "Phase 6 — Collapse the flags": the flag-fate
  table + "Open questions — RESOLVED" (FD1/FD2).
- `sprints/DEFERRED_VERIFICATION.md` — §3 (Ralph/V2), §9 (issue/V3); V1 is the
  ENGINE+TOOLS+PERSONAS big run.
- `.ai/context/workflow.md` — the Opus↔Sonnet handoff protocol.

## Working tree
- HEAD `1449d65` — the known-good `devcontainer.json` is committed (durable).
  Uncommitted: only this `.ai/next-steps.md` regeneration (`.ai/state.json` is
  git-ignored). Commit it before switching sessions so `/resume` sees a clean
  tree matching `last_commit`.
