# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 6 — sprint `27_phase6_flip_block`: the flag collapse is MERGED (`1217f79`, PR #28).**
The migration's flag era is over — there is **one path, not N**. What remains of sprint 27
is **V3** and the two tasks it gates.

## Just done (Opus/Architect, 2026-07-11)
- **All four migration flags DELETED**, with the classic paths they selected — not kept as
  live break-glass branches (decision **FD2**). Each was gated on its host verification
  passing first (V1; V2 re-attempt #8). Merged as **`1217f79`** (squash of `ec8b0e5`
  ENGINE → `adb20b3` TOOLS → `56c3824` PERSONAS → `3ea8106` CODER → `29128ed` docs):
  - `LOOP_ENGINE_ENGINE` → `run_loop` + the classic-vs-graph parity harness
  - `LOOP_ENGINE_TOOLS` → the in-process `CODER_TOOLS`/`_execute_tool` dispatch
  - `LOOP_ENGINE_PERSONAS` → the three classic document personas + their embedded
    prompts; **`prompts/` is now the sole source of truth**
  - `LOOP_ENGINE_CODER` → `CoderIacPersona` + `CoderGate`
- **Survivors:** `LOOP_ENGINE_ISOLATION` and `LOOP_ENGINE_RALPH_MAX_ITERS` — both genuine
  runtime config, never old-vs-new. `build_default_loop()` is one unbranched wiring.
- **Recovery point:** tag **`pre-phase6-classic`** (pushed). FD2 is git-revert, not a flag.
- **Task 5 (`State.artifacts` strip) DEFERRED — decision FD3.** Its premise was false: the
  plan assumed deleting `run_loop` leaves the engine the sole reader of `state.artifacts`,
  but **the engine was never a reader** — every persona and gate indexes the inline dict
  directly, `artifact_refs` is a write-only mirror, and `get_artifact` has **zero callers**.
  It is a behavior-changing refactor (disk I/O in the hot path V1/V2 just verified, plus a
  cwd hazard under `run_in_tree`/`flows/maintenance`), not a deletion. **Needs its own
  sprint + design pass.**
- **Task 6 was never a separate pass** — it fell out of the deletions: a
  `build_default_loop()` that cannot read a flag cannot branch on one.

## Next
1. **V3 — the forced issue-escalation host round-trip.** The last unstarted host
   verification: deliberately trigger a pause-for-issue so the run files a *real* GitHub
   issue through the `issue` MCP server, answer it with an ` ```answers ` comment, resume
   through the MCP reader. Human-operated (real `gh` auth, real budget, real GitHub side
   effects — clean up the scratch repo/issue afterward). **Opus/Architect, host session.**
2. V3 gates **both** remaining sprint-27 tasks: **Task 8** (issue-path flip onto MCP,
   carrying Sprint 26 findings R1–R7) and **Task 9** (delete `DEFERRED_VERIFICATION.md`,
   close Phase 6).
3. Then: the deferred **`State.artifacts` strip** as its own sprint (see FD3).
4. `/archive-sprint` for sprint 27 only once Tasks 8–9 land — **it is not done yet.**

## HITL gate
**No open gate.** PR #28 merged (the owner's merge *is* the approval). Standing gate: every
sprint lands via a PR into `feat/mcp-langgraph-migration`; Claude never merges or
force-pushes.

## Breaking changes now on the integration branch
- **Public API:** `loop_engine.run_loop` → **`loop_engine.run_graph_loop`** (same signature
  and return contract).
- **Default-loop stage names changed** (`PMPersona` → `PMGenerator`, `ArchitecturePersona` →
  `ArchitectureGenerator`, the Coder → `RalphCoderPersona`), so **snapshot filenames changed
  too** — a snapshot produced before `1217f79` resumes under different stage-name
  expectations.

## Pointers
- `sprints/27_phase6_flip_block/sprint_plan.md` — STATUS block at the top: Tasks 0–4/6/7
  done, 5 deferred (FD3), 8–9 open on V3.
- `docs/migration_roadmap.md` — flag-fate table (four DELETED with commits, one KEPT),
  decisions log (FD1/FD2/**FD3**), NEXT ACTION.
- `sprints/DEFERRED_VERIFICATION.md` — V1 PASS(qualified); V2 PASS; **V3 not started**.
- `.ai/context/workflow.md` — the PR-gated integration protocol.
- `docs/backlog.md` — BL-1..BL-5.

## Working tree
- `feat/mcp-langgraph-migration` is at `1217f79`; 499 tests green there. All sprint branches
  through #28 are merged and deleted — **PRs squash-merge, so a merged branch is dead**;
  always cut new work from updated `origin/feat/mcp-langgraph-migration`.
- Untracked `scratch/` holds the V2 harness + run-#8 evidence; it stays out of all commits.
- `.ai/state.json` is git-ignored (local mirror); `.ai/next-steps.md` **is tracked** and
  lands via a PR like any other file.
