# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 6 — sprint `27_phase6_flip_block`: V3 is DONE — `PASS (qualified)`. Tasks 8 and 9
are UNBLOCKED.** The flag collapse merged at `1217f79` (PR #28). V3 was the last gate on the
sprint's remaining two tasks.

## Just done (Opus/Architect, 2026-07-11/12)
- **V3a PASS** ($0, no LLM) — the issue server exposed exactly `{create_issue, read_issue}`;
  a real issue was filed through it with the `loop-engine/needs-human` label; and
  **`read_issue` via MCP returned a payload byte-identical to `gh issue view` run directly**
  — the one thing Sprint 26's hermetic suite structurally could not prove.
- **V3b PASS (qualified)** (≈$0.13 total, well under the $1/$5 caps) — the engine-level
  round-trip. A forced pause filed **real issue #5 through the MCP server**; a human answered
  it; `cli.resume` **read it back through the MCP reader**, parsed the answers, marked both
  questions `resolved_by: human:5`, folded them into the PM (which re-ACCEPTed), and **the
  run advanced past the stage it paused on** (stage 0 → stage 1, a real
  `architecture_definition` produced). Both seams proven against a real `gh`, real issues,
  and the real server subprocess.
- **Recorded in `sprints/DEFERRED_VERIFICATION.md`** (the V3 section), with the four
  findings below. **`docs/backlog.md` gains BL-7** (R9 — it must outlive Task 9, which
  deletes `DEFERRED_VERIFICATION.md`).

### The four findings V3 produced
- **R2 — CONFIRMED LIVE** (was inferred). The resumed run **re-paused** at the Architect
  stage on 6 genuine new questions, and that second issue (**#6**) was filed through the
  **classic in-process `gh` path, not MCP** — because `cli.resume` threads no `issue_filer`
  into its inner `run_graph_loop`. Task 8 now has an *observed* motivation.
- **R8 — confirmed, did not leak.** `create_issue` shells `gh` with no `--repo`, so the
  destination follows the cwd. V3 stayed clean only because cwd was the scratch clone;
  `glunk-works/loop-engine` still has exactly escalation issues **#16/#19/#21**. The leak is
  latent, not absent. Route into Task 8: make the issue destination **explicit**.
- **R9 — NEW, product defect → `docs/backlog.md` BL-7.** *The PM stage cannot escalate a
  requirements contradiction.* Given a deliberately unsatisfiable doc, the PM **correctly
  identified every contradiction**, wrote them into `risks_and_assumptions` — and the gate
  **ACCEPTed anyway**. Three things compose: `CriticGate` is purely *structural* (no LLM; its
  only consistency check is `in_scope == out_of_scope`), the PM's artifact is JSON with no
  `open_questions` key, and `configs/pm.yaml` sets `extract_open_questions: false`. The stage
  whose job is to interrogate requirements is the one stage that cannot ask. **Does not gate
  Tasks 8/9.**
- **R10 — NEW, minor → Task 8.** *A run cannot be paused and resumed under different
  isolation modes.* `cli.resume` calls `worktree_run(reuse=True)`, which hard-fails if the
  worktree doesn't exist — and an `ISOLATION=none` pause creates none. Honest failure, but
  undocumented; the V3 plan's own `none`-pause/`container`-resume advice walked into it.

## Next
1. **Open the PR** for this V3 record (branch off updated `origin/feat/mcp-langgraph-migration`).
2. **Task 8 — flip the issue path onto MCP**, carrying **R1–R7 + R8 + R10**. Sonnet/Coder
   implements; the spec is now fully determined by the V3 record.
3. **Task 9** — delete `sprints/DEFERRED_VERIFICATION.md`, close Phase 6.
4. Then: the deferred **`State.artifacts` strip** as its own sprint (FD3).
5. `/archive-sprint` for sprint 27 once Tasks 8–9 land.

**Model: Sonnet/Coder** for Task 8 (an already-defined spec). Opus/Architect returns for the
HITL review of that diff.

## HITL gate
**No open gate.** Standing gate: every sprint lands via a PR into
`feat/mcp-langgraph-migration`; the owner's merge is the approval; Claude never merges or
force-pushes.

## Live external state — needs cleanup (HUMAN ACTION)
- **`glunk-works/loop-engine-v3-scratch`** (private) is **live**, holding issues **#1–#6**
  and one seed commit on `main`. At cleanup: **delete the repo in the GitHub UI**, then
  remove it from the fine-grained PAT's repository list. The PAT deliberately has **no
  `Administration` permission**, so it cannot delete repos — that stays a human checkpoint on
  the one irreversible action. *(The PAT did turn out to hold `Contents: Write` on it, which
  the V3 plan's Option A had not expected — worth trimming when you edit the repo list.)*
- Confirmed clean: `glunk-works/loop-engine` escalation issues are still exactly
  **#16, #19, #21**. Nothing new leaked.

## Pointers
- `sprints/27_phase6_flip_block/sprint_plan.md` — Tasks 0–4/6/7 done, 5 deferred (FD3),
  **8–9 now unblocked**. Its security consideration (5) is **wrong** that V3 must run under
  `container` because it "executes model-generated code" — a PM-stage pause executes none.
  Correct it when Task 8/9 touch the plan.
- `sprints/DEFERRED_VERIFICATION.md` — V1 PASS(qualified); V2 PASS; **V3 PASS (qualified)**.
  Task 9 deletes this file.
- `docs/migration_roadmap.md` — flag-fate table, decisions log (FD1/FD2/FD3), NEXT ACTION.
- `.ai/context/workflow.md` — the PR-gated integration protocol.

## Working tree
- `feat/mcp-langgraph-migration` is at `f556387`. Sprint branches squash-merge, so a merged
  branch is dead — always cut new work from updated `origin/feat/mcp-langgraph-migration`.
- Untracked `scratch/` holds the V2/V3 harnesses + evidence; it stays out of all commits.
- `.ai/state.json` is git-ignored (local mirror); **`.ai/next-steps.md` is tracked** and
  lands via a PR like the previous cursor resyncs (#27, #29).
