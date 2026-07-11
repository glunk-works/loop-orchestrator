# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 6 — sprint `27_phase6_flip_block` — `planned_host_gated`, now with a
prerequisite Ralph-hardening sprint owed first.**
V2 was re-attempted on a daemon-bearing host (#6, 2026-07-11). **Staging is finally
validated**, but V2 still did **not** reach `COMPLETED` — Ralph escalated on a
self-inflicted over-specified test. New blocking finding **F-RALPH-OVERSPEC-TEST**
opened. V2 stays OPEN, now gated on that fix. **No deletion may land.**

## Just done (Opus/Architect host session, 2026-07-11)
- **V2 re-attempt #6 run.** Config `langgraph`+`mcp`+`declarative`+`ralph`+`container`
  against the minimal 2-fn `textkit` spec. Result: `AWAITING_ISSUE`, **$3.29/$5.00**,
  run_id `0d5e3f3c274d414e988ac295a8d4bddb`. Reached the container Ralph coder + a
  full sandboxed tool loop, then escalated.
- **Staging cracked (three fixes):** (1) rebuilt `loop-engine-dev:latest` **with
  ruff** (`Dockerfile` dev stage) — closes the F-CODER-NO-LINT host obligation
  (`python -m ruff` now resolves in-container); (2) **injected non-crashing
  `issue_filer`** (the Seuss27 PAT is scoped only to `glunk-works/loop-engine`, so a
  throwaway scratch **remote was not creatable** — the real-remote staging option is
  blocked; injected-filer is the working path); (3) invoked via the **absolute
  loop-engine hatch-env python**, not `hatch run` (which is cwd-sensitive and tried
  to build the scratch `textkit` tree). The injected filer paused cleanly (no `gh`
  crash) — staging approach proven.
- **New finding F-RALPH-OVERSPEC-TEST** recorded in `DEFERRED_VERIFICATION.md`:
  Ralph wrote **correct** product code but authored a test asserting a private module
  internal (`_NON_ALNUM_RUN`) via a broken import form, then **escalated** (rigid
  task-scoping) rather than self-fixing a one-line unspecified test. Repo-owner
  decision: stop spending budget, open the finding, fix in a new sprint.

## Next
1. **Plan a new Ralph-hardening sprint (Opus/Architect).** Steer Ralph away from
   tests **beyond the spec's enumerated cases** (esp. private/underscore internals +
   import mechanics) and toward **self-fixing its own suite before escalating** across
   self-imposed task boundaries. Candidate surfaces: the Ralph coder **prompt**
   (test-scope guardrail) and/or the **`RalphCoderGate`/escalation guard** (a red gate
   on a self-authored out-of-spec test → a fix increment, not a human). Then
   **Sonnet** implements.
2. **Fresh V2 re-attempt** (host) after the fix — observe terminal `COMPLETED` within
   budget. Reuse the staging recipe above (harness `scratch/v2_run_harness.py`, tree
   `scratchpad/v2_tree`, `LOOP_ENGINE_DEV_IMAGE=loop-engine-dev:latest`, abs env python).
3. **On V2 PASS:** the subtractive sprint-27 flag deletions unblock (Task 4
   `CODER=ralph` gated on V2; Tasks 1–3 on V1; Task 8 on V3).

## HITL gate
No outstanding **diff** review owed — nothing committed this session. The V2 #6
PASS/FAIL judgement is already taken (repo owner): it is a **FAIL** (escalated, not
`COMPLETED`) → open F-RALPH-OVERSPEC-TEST, do **not** flip `CODER=ralph`. Open
critical-path gates: V2 host `COMPLETED` (unobserved, now gated on the Ralph fix) and
V3 (not started).

## Pointers
- `sprints/DEFERRED_VERIFICATION.md` — V1 PASS(qualified); **V2 OPEN** (staging
  validated via injected filer, escalated not COMPLETED); **F-RALPH-OVERSPEC-TEST
  OPEN** (blocks V2→`CODER=ralph`); F-CODER-NO-LINT host obligation (ruff-in-image)
  closed; V3 not started.
- `sprints/27_phase6_flip_block/sprint_plan.md` — the flip block (planned, host-gated);
  Task 4 gated on V2, which is now gated on the Ralph-hardening fix.
- `docs/backlog.md` — BL-1..BL-5 (BL-4 Ralph liveness watcher is adjacent but distinct
  from F-RALPH-OVERSPEC-TEST).

## Working tree
- HEAD `60ecd54`. **Uncommitted committable delta:** `Dockerfile` (ruff in dev stage)
  + `sprints/DEFERRED_VERIFICATION.md` (F-RALPH-OVERSPEC-TEST + V2 #6 note) + this
  cursor. Untracked `scratch/` (V2 specs/logs/harness/pubkey) and `scratchpad/v2_tree`
  remain out of all commits. `.ai/state.json` is git-ignored (local mirror only).
- Aside (not migration work): GitHub shows commits **Unverified** — they ARE signed
  locally (ed25519 `F1AAE…6AB8005D`, jgroves27@gmail.com); the public key just needs
  uploading to the GitHub account owning that verified email. Pubkey exported to
  `scratch/jgroves27-gpg-pubkey.asc`. See `[[gpg-signing-forwarded-agent]]`.
