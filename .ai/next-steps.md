# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 6 — sprint `27_phase6_flip_block`: V3 is DONE (`PASS (qualified)`, merged as PR #30,
`8a8b59f`). Tasks 8 and 9 are UNBLOCKED — and they are the last of the sprint.**

## Just done (Opus/Architect, 2026-07-11/12)
- **V3 ran and passed** against a real `gh`, real GitHub issues, and the real issue MCP
  server subprocess (≈$0.13, well under the $1/$5 caps). **V3a**: the server exposed exactly
  `{create_issue, read_issue}` and `read_issue` through MCP returned a payload
  **byte-identical to `gh issue view` run directly** — the one thing Sprint 26's hermetic
  suite structurally could not prove. **V3b**: a forced pause filed a **real issue through
  the MCP server**, a human answered it, `cli.resume` **read it back through the MCP reader**,
  resolved both questions (`resolved_by: human:5`), folded them into the PM, and the run
  **advanced past the stage it paused on**. Both `DEFERRED_VERIFICATION.md` §9 seams cleared.
- *Qualified because* the run re-paused at the Architect on 6 genuine new questions instead of
  reaching `COMPLETED` — the escalation ladder working, not a seam defect. The Coder was never
  reached, so no model-generated code executed.
- **Findings** (full write-ups in the `DEFERRED_VERIFICATION.md` V3 section): **R2 is now
  confirmed live** — the re-paused run filed its second issue through the **classic `gh` path,
  not MCP**, because `cli.resume` threads no `issue_filer`. **R8** confirmed but did not leak
  (loop-engine still holds exactly escalation issues #16/#19/#21). **R10** is new: a run can't
  be paused and resumed under different isolation modes. **R9** is new and is a *product*
  defect, so it went to **`docs/backlog.md` BL-7** — it must outlive Task 9.

## Next
1. **Task 8 — flip the issue path onto MCP** and delete the classic direct calls. Carry
   **R1–R7** (`docs/migration_roadmap.md` ~801–838; sprint plan line 34 pins that R1/R2/R3/R4/R7
   must land *inside* Task 8, with R5/R6 folded in for coherence) **plus R8 and R10**.
2. **Task 9** — delete `sprints/DEFERRED_VERIFICATION.md`, close Phase 6. Anything that must
   survive has to move out first (R9 already did).
3. While in the sprint plan: **correct security consideration (5)**. It claims V3 must run under
   `ISOLATION=container` because it "executes model-generated code" — **wrong for a pause leg**,
   which is upstream of the Coder and executes none.
4. Then: the deferred **`State.artifacts` strip** as its own sprint (FD3).
5. `/archive-sprint` for sprint 27 only once Tasks 8–9 land.

**Model: Sonnet/Coder.** Task 8 is an already-defined spec — the V3 record determines it.
Opus/Architect returns for the HITL review of that diff.

## HITL gate
**No open gate.** Standing gate: every sprint lands via a PR into
`feat/mcp-langgraph-migration`; the owner's merge is the approval; Claude never merges or
force-pushes.

## Live external state — cleanup owed (HUMAN ACTION, deferred by owner's choice)
- **`glunk-works/loop-engine-v3-scratch`** (private) is **still live**, holding issues **#1–#6**
  and a seed commit on `main`. Cleanup: **delete it in the GitHub UI**, then remove it from the
  fine-grained PAT's repository list. The PAT deliberately has **no `Administration`
  permission**, so the one irreversible action stays a human checkpoint. It did turn out to
  carry **`Contents: Write`**, which the V3 plan's least-privilege Option A had not expected —
  worth trimming while editing the repo list.
- Confirmed clean: `glunk-works/loop-engine` escalation issues are still exactly
  **#16, #19, #21**. Nothing leaked.

## Pointers
- `sprints/27_phase6_flip_block/sprint_plan.md` — Tasks 0–4/6/7 done, 5 deferred (FD3), **8–9
  open and unblocked**.
- `sprints/DEFERRED_VERIFICATION.md` — V1 PASS(qualified); V2 PASS; **V3 PASS (qualified)**,
  with R2/R8/R9/R10 written up. **Task 9 deletes this file.**
- `docs/migration_roadmap.md` — flag-fate table, decisions log (FD1/FD2/FD3), findings R1–R7.
- `docs/backlog.md` — **BL-7** (R9: the PM stage cannot escalate a requirements contradiction).
  Not part of sprint 27.
- `.ai/context/workflow.md` — the PR-gated integration protocol.

## Working tree
- `feat/mcp-langgraph-migration` is at **`8a8b59f`**. Sprint branches squash-merge, so a merged
  branch is dead — always cut new work from updated `origin/feat/mcp-langgraph-migration`.
- Untracked `scratch/` holds the V2/V3 harnesses + evidence; it stays out of all commits. If
  Task 8 re-runs V3 after the flip: both legs must share one isolation mode (**R10**), and the
  unsatisfiable-doc trigger does **not** work (**R9**) — use `--force-gate`.
- `.ai/state.json` is git-ignored (local mirror); **`.ai/next-steps.md` is tracked** — this
  regeneration is uncommitted; let it ride the Task 8 PR.
