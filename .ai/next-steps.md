# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 6 — sprint `27_phase6_flip_block`: the flag deletions are DONE and in review.**
**PR #28 is open, CLEAN, and awaiting the owner's merge.** The migration's flag era is
over: there is one path, not N.

## Just done (Opus/Architect, 2026-07-11)
- **All four migration flags DELETED**, with the classic paths they selected — not kept
  as live break-glass branches (decision **FD2**). Each gated on its host verification
  passing first (V1; V2 re-attempt #8):
  - `LOOP_ENGINE_ENGINE` → `run_loop` + the classic-vs-graph parity harness (`ec8b0e5`)
  - `LOOP_ENGINE_TOOLS` → the in-process `CODER_TOOLS`/`_execute_tool` dispatch (`adb20b3`)
  - `LOOP_ENGINE_PERSONAS` → `PMPersona`/`ArchitecturePersona`/`AgileSprintBreakdownPersona`
    + their embedded prompts; `prompts/` is now the sole source of truth (`56c3824`)
  - `LOOP_ENGINE_CODER` → `CoderIacPersona` + `CoderGate` (`3ea8106`)
- **Task 0:** tagged **`pre-phase6-classic`** (pushed) — the FD2 recovery point.
- **Task 6 fell out of the deletions**, it was never a separate pass: a
  `build_default_loop()` that cannot read a flag cannot branch on one. `loop.py` is now
  one unbranched wiring.
- **Task 7:** docs reconciled (`29128ed`) — CLAUDE.md, README, `.ai/context/modules.md`,
  roadmap flag-fate table + status row + NEXT ACTION.
- **Task 5 (the `artifacts` strip) DEFERRED — decision FD3.** Its premise was false: the
  plan assumed deleting `run_loop` leaves the engine the sole reader of `State.artifacts`,
  but **the engine was never a reader** — every persona and gate indexes the inline dict
  directly, `artifact_refs` is a write-only mirror, and `get_artifact` has **zero callers**.
  It is a behavior-changing refactor (disk I/O in the hot path V1/V2 just verified, plus a
  cwd hazard under `run_in_tree`), not a deletion. Needs its own sprint + design pass.
- **Coverage salvage (the real hazard in a subtractive sprint).** Three deletions would
  have silently dropped the only tests for code that *survives*; each was re-homed:
  `fold_answers` (still driven by `cli.resume`), the sprint-block adapter (now in
  `declarative/services.finalize_sprint_blocks`), and three paths `RalphCoderGate` shares
  with the deleted `CoderGate`. Also salvaged the Coder prompt's sprint-30
  F-RALPH-OVERSPEC-TEST guardrail, which lived in a file importing the classic templates.
- Gate: **499 passed**, lint/format/audit clean, `sbom.json` unchanged. Boundary tests hold
  (subprocess surfaces, MCP server disjointness, keyring, `extra="forbid"`).

## Next
1. **Owner merges PR #28.** (Claude never merges.)
2. **V3 — the forced issue-escalation host round-trip.** The last unstarted host
   verification: deliberately trigger a pause-for-issue so the run files a *real* GitHub
   issue through the `issue` MCP server, answer it with an ` ```answers ` comment, resume
   through the MCP reader. Human-operated (real `gh` auth, real budget, real side effects
   — clean up the scratch repo/issue afterward). **Opus/Architect, host session.**
3. V3 gates **both** remaining sprint-27 tasks: **Task 8** (issue-path flip onto MCP,
   carrying Sprint 26 findings R1–R7) and **Task 9** (delete `DEFERRED_VERIFICATION.md`,
   close Phase 6).
4. Then: the deferred **`State.artifacts` strip** as its own sprint (see FD3).

## HITL gate
**OPEN — PR #28** (`sprint/27-flag-collapse` → `feat/mcp-langgraph-migration`):
MERGEABLE/CLEAN, all 7 checks green, Opus HITL review posted as a comment. Awaiting the
owner's merge, which *is* the approval. Standing gate: every sprint lands via a PR into
`feat/mcp-langgraph-migration`; Claude never merges or force-pushes.

## Breaking changes in flight (worth knowing on resume)
- **Public API:** `loop_engine.run_loop` → `loop_engine.run_graph_loop` (same signature).
- **Default-loop stage names changed** (`PMPersona` → `PMGenerator`, …), so snapshot
  filenames did too — a pre-PR-#28 snapshot resumes under different stage-name
  expectations.

## Pointers
- `sprints/27_phase6_flip_block/sprint_plan.md` — has a STATUS block: 0–4/6/7 done,
  5 deferred, 8–9 open on V3.
- `docs/migration_roadmap.md` — flag-fate table (four DELETED, one KEPT), decisions log
  (FD1/FD2/**FD3**), NEXT ACTION.
- `sprints/DEFERRED_VERIFICATION.md` — V1 PASS(qualified); V2 PASS; **V3 not started**.
- `.ai/context/workflow.md` — the PR-gated integration protocol.
- `docs/backlog.md` — BL-1..BL-5.

## Working tree
- On `sprint/27-flag-collapse` (pushed, `29128ed`). **Do not cut new work from it** — wait
  for the merge, then branch from updated `origin/feat/mcp-langgraph-migration` (PRs
  squash-merge, so a merged branch is dead).
- Untracked `scratch/` holds the V2 harness + run-#8 evidence; it stays out of all commits.
- `.ai/state.json` is git-ignored (local mirror); `.ai/next-steps.md` **is tracked** and
  lands via a PR like any other file.
